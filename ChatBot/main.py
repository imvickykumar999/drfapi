"""
telegram_weather_bot.py

Telegram webhook that uses:
- InMemorySessionService for per-chat (and per-topic) sessions
- ADK Runner to call your weather_agent (with get_weather tool)
- Groq via LiteLlm (primary + fallbacks)
- Flask (sync) + asyncio to run async ADK code
- Optional voice transcription via Groq Whisper

Install:
    pip install flask requests python-dotenv

Plus your stack:
    google-adk (your ADK), WeatherAPI, groq, litellm

Env (.env):
    TELEGRAM_BOT_TOKEN=123456:ABC...
    GROQ_API_KEY=gsk_...
    PUBLIC_BASE_URL=https://<your-ngrok-or-domain>
    # optional: WEBHOOK_SECRET=some-long-random-string
"""

import os
import re
import time
import asyncio
import warnings
import logging
import random
import requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify, abort

# --- Your ADK stack ---
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from Portfolio import get_home, get_about, get_skilled, get_skills, get_work
from groq import Groq

# Optional LiteLLM exceptions
try:
    import litellm  # type: ignore
except Exception:
    litellm = None

# ----------------------------
# Setup & configuration
# ----------------------------
load_dotenv()
warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "change-me-please-32-bytes")

if not BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")
if not GROQ_KEY:
    raise RuntimeError("GROQ_API_KEY is not set")
if not PUBLIC_BASE_URL:
    raise RuntimeError("PUBLIC_BASE_URL is not set")

os.environ["GROQ_API_KEY"] = GROQ_KEY  # LiteLlm expects it
groq_client = Groq(api_key=GROQ_KEY)

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{PUBLIC_BASE_URL}{WEBHOOK_PATH}"

# ----------------------------
# Models & Agent (Groq-first)
# ----------------------------

GROQ_PRIMARY = "groq/llama-3.3-70b-versatile"
GROQ_FALLBACKS = [
    "groq/llama3-8b-8192",
    "groq/gemma2-9b-it",   # ✅ valid replacement
]

DEFAULT_MAX_TOKENS = 256

def make_model(model_name: str) -> LiteLlm:
    """Create a LiteLlm model handle (Groq OpenAI-compatible)."""
    return LiteLlm(
        model=model_name,
        api_key=GROQ_KEY,
        max_tokens=DEFAULT_MAX_TOKENS,
        timeout=30,          # a bit generous; we do our own retries/backoff
        num_retries=0,
    )

weather_agent = Agent(
    name="weather_agent_v1",
    model=make_model(GROQ_PRIMARY),
    description="You are blog assistant of imvickykumar999 company.",
    instruction=(
        "You are a helpful assistant. "
        "When the user asks for specific information, "
        "use the available tool(s) to query the appropriate API. "
        "If the tool returns an error, inform the user politely. "
        "If the tool is successful, present the information clearly and concisely. "
    ),
    tools=[get_home, get_about, get_skilled, get_skills, get_work, ],
)

# ----------------------------
# Session service & runner
# ----------------------------
session_service = InMemorySessionService()
APP_NAME = "blog_assistant_app"

runner = Runner(
    agent=weather_agent,
    app_name=APP_NAME,
    session_service=session_service,
)

# Track sessions if your ADK version lacks get_session()
_seen_sessions = set()

async def ensure_session(user_id: str, session_id: str):
    """Get-or-create session; avoid resetting history each message."""
    try:
        sess = await session_service.get_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id
        )
        if not sess:
            await session_service.create_session(
                app_name=APP_NAME,
                user_id=user_id,
                session_id=session_id
            )
    except AttributeError:
        # Older ADK: emulate get-or-create
        key = (APP_NAME, user_id, session_id)
        if key not in _seen_sessions:
            await session_service.create_session(
                app_name=APP_NAME,
                user_id=user_id,
                session_id=session_id
            )
            _seen_sessions.add(key)

# ----------------------------
# Helpers: rate limit / transient handling & model fallback
# ----------------------------
RATE_LIMIT_PATTERN = re.compile(r"try again in ([\d.]+)s", re.IGNORECASE)

def _is_rate_limit_error(e: Exception) -> bool:
    if litellm and isinstance(e, getattr(litellm, "RateLimitError", tuple())):
        return True
    msg = f"{type(e).__name__}: {e}"
    return "rate limit" in msg.lower() or "rate_limit_exceeded" in msg.lower()

def _is_transient_error(e: Exception) -> bool:
    if litellm:
        transient_types = (
            getattr(litellm.exceptions, "ServiceUnavailableError", tuple()),
            getattr(litellm.exceptions, "APIConnectionError", tuple()),
            getattr(litellm.exceptions, "InternalServerError", tuple()),
            getattr(litellm.exceptions, "APIError", tuple()),
        )
        if isinstance(e, transient_types):
            return True
    msg = str(e).lower()
    return any(k in msg for k in ["service unavailable", "503", "bad gateway", "502", "gateway timeout", "504", "temporarily unavailable", "connection reset", "connection aborted"])

async def _backoff_sleep(err_msg: str, attempt: int):
    # exponential + jitter
    base = min(2 ** attempt, 20)
    jitter = random.uniform(0, 0.5 * base)
    await asyncio.sleep(base + jitter)

async def _swap_model_to_fallback(agent: Agent, used: set) -> bool:
    for cand in GROQ_FALLBACKS:
        if cand not in used:
            agent.model = make_model(cand)
            logging.info("[Model Fallback] Switched to: %s", cand)
            used.add(cand)
            return True
    return False

async def ask_agent_async(query: str, user_id: str, session_id: str) -> str:
    """
    Runs the ADK runner with retries + fallbacks.
    Returns the final response text to send back to Telegram.
    Uses InMemorySessionService keyed by (app_name, user_id, session_id).
    """
    await ensure_session(user_id, session_id)

    content = types.Content(role="user", parts=[types.Part(text=query)])
    final_response_text = "I couldn't produce a response."
    max_attempts = 6
    used_models = {GROQ_PRIMARY}
    attempt = 0

    while attempt < max_attempts:
        attempt += 1
        try:
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=content
            ):
                if event.is_final_response():
                    if getattr(event, "content", None) and event.content.parts:
                        final_response_text = event.content.parts[0].text
                    elif getattr(event, "actions", None) and getattr(event.actions, "escalate", None):
                        final_response_text = f"Agent escalated: {event.error_message or 'No specific message.'}"
                    break
            return final_response_text

        except Exception as e:
            msg = f"{type(e).__name__}: {e}"
            if _is_rate_limit_error(e) or _is_transient_error(e):
                logging.warning("[Transient] Attempt %s/%s: %s", attempt, max_attempts, msg)
                await _backoff_sleep(str(e), attempt)
                if await _swap_model_to_fallback(runner.agent, used_models):
                    continue
                # else: retry same model after backoff
                continue

            logging.exception("[Error] Unhandled exception while asking agent")
            return "Sorry, something went wrong while generating the answer."

    return "The assistant is temporarily unavailable (provider error). Please try again shortly."

# ----------------------------
# Telegram plumbing
# ----------------------------
app = Flask(__name__)

def session_keys(message: dict):
    """
    Define stable per-chat (and per-topic) session keys to preserve memory.
    - In groups with topics, include message_thread_id so each topic has separate memory.
    """
    chat_id = message["chat"]["id"]
    thread_id = message.get("message_thread_id")  # None if not a forum topic
    # Per-chat memory (all users in the chat share it), separated by topic if present:
    user_id = f"tg_chat_{chat_id}"
    session_id = f"tg_chat_{chat_id}_{thread_id or 'main'}"
    return user_id, session_id

def set_webhook():
    url = f"{BASE_URL}/setWebhook"
    payload = {
        "url": WEBHOOK_URL,
        "secret_token": WEBHOOK_SECRET,     # verifies Telegram origin
        "allowed_updates": ["message"],
    }
    r = requests.post(url, json=payload, timeout=15)
    r.raise_for_status()
    return r.json()

def send_message(chat_id: int, text: str, retries: int = 3):
    url = f"{BASE_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    for i in range(retries):
        try:
            requests.post(url, json=payload, timeout=20)
            return
        except requests.RequestException:
            if i == retries - 1:
                logging.exception("Failed to send message to Telegram after retries")
            else:
                time.sleep(2 * (i + 1))

def transcribe_voice(file_name: str, file_content: bytes) -> str:
    """Use Groq Whisper to transcribe Telegram OGG voice notes."""
    try:
        transcription = groq_client.audio.transcriptions.create(
            file=(file_name, file_content),
            model="whisper-large-v3",
            response_format="verbose_json",
        )
        return transcription.text
    except Exception:
        logging.exception("Groq transcription failed")
        return "Sorry, I'm having trouble transcribing your audio."

@app.route(WEBHOOK_PATH, methods=["POST"])
def telegram_webhook():
    # Verify Telegram secret (optional but recommended)
    secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if secret and secret != WEBHOOK_SECRET:
        return abort(401)

    update = request.get_json(silent=True) or {}
    message = update.get("message")
    if not message:
        return jsonify({"status": "ignored"}), 200

    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    if not chat_id:
        return jsonify({"status": "ignored"}), 200

    user_id, session_id = session_keys(message)

    # TEXT
    if "text" in message:
        text = (message.get("text") or "").strip()
        reply = asyncio.run(ask_agent_async(text, user_id=user_id, session_id=session_id))
        send_message(chat_id, reply)
        return jsonify({"status": "ok"}), 200

    # VOICE: fetch -> transcribe -> ask agent
    if "voice" in message:
        try:
            file_id = message["voice"]["file_id"]
            info = requests.get(f"{BASE_URL}/getFile", params={"file_id": file_id}, timeout=15).json()
            if not info.get("ok"):
                send_message(chat_id, "Sorry, could not retrieve the audio file.")
                return jsonify({"status": "ok"}), 200

            file_path = info["result"]["file_path"]
            file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
            ogg = requests.get(file_url, timeout=30).content

            text = transcribe_voice("voice.ogg", ogg)
            reply = asyncio.run(ask_agent_async(text, user_id=user_id, session_id=session_id))
            send_message(chat_id, reply)
            return jsonify({"status": "ok"}), 200

        except Exception:
            logging.exception("Voice handling failed")
            send_message(chat_id, "Sorry, I couldn't process that voice note.")
            return jsonify({"status": "ok"}), 200

    if "sticker" in message:
        sticker_info = message["sticker"]
        emoji = sticker_info.get("emoji", "")
        if emoji:
            reply = asyncio.run(ask_agent_async(emoji, user_id=user_id, session_id=session_id))
            send_message(chat_id, reply)
            return jsonify({"status": "ok"}), 200
        return jsonify({"status": "ignored"}), 200

    # Ignore other types
    return jsonify({"status": "ignored"}), 200

@app.get("/")
def health():
    return jsonify({"ok": True})

@app.get("/install_webhook")
def install_webhook():
    try:
        result = set_webhook()
        return jsonify(result)
    except Exception as e:
        logging.exception("Failed to set webhook")
        return jsonify({"ok": False, "error": str(e)}), 500

def sanity_check():
    """Optional: quick outbound check so failures are obvious at startup."""
    try:
        requests.get("https://api.groq.com", timeout=10)
        requests.get("https://api.telegram.org", timeout=10)
        logging.info("Network sanity check passed.")
    except Exception as e:
        logging.error("Network sanity check failed: %s", e)

if __name__ == "__main__":
    sanity_check()
    # IMPORTANT: single process, no reloader; InMemorySessionService lives in-process
    app.run(host="0.0.0.0", port=8000, debug=False, use_reloader=False)
