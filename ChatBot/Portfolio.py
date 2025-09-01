import logging
import requests

logging.basicConfig(level=logging.DEBUG)

BASE_URL = "https://drfapi.pythonanywhere.com"

def get_api_overview(query: str = "") -> dict:
    try:
        resp = requests.get(f"{BASE_URL}/api/", timeout=30)
        resp.raise_for_status()
        data = resp.json()
        logging.debug(f"GET /api/ -> {data}")
        return {"status": "success", "report": data}
    except requests.exceptions.Timeout:
        return {"status": "error", "report": "The request timed out. Please try again later."}
    except requests.exceptions.RequestException as e:
        return {"status": "error", "report": f"An error occurred: {str(e)}"}

def get_home(query: str = "") -> dict:
    try:
        resp = requests.get(f"{BASE_URL}/api/home/", timeout=30)
        resp.raise_for_status()
        data = resp.json()
        logging.debug(f"GET /api/home/ -> {data}")
        return {"status": "success", "report": data}
    except requests.exceptions.Timeout:
        return {"status": "error", "report": "The request timed out. Please try again later."}
    except requests.exceptions.RequestException as e:
        return {"status": "error", "report": f"An error occurred: {str(e)}"}

def get_about(query: str = "") -> dict:
    try:
        resp = requests.get(f"{BASE_URL}/api/about/", timeout=30)
        resp.raise_for_status()
        data = resp.json()
        logging.debug(f"GET /api/about/ -> {data}")
        return {"status": "success", "report": data}
    except requests.exceptions.Timeout:
        return {"status": "error", "report": "The request timed out. Please try again later."}
    except requests.exceptions.RequestException as e:
        return {"status": "error", "report": f"An error occurred: {str(e)}"}

def get_skilled(query: str = "") -> dict:
    try:
        resp = requests.get(f"{BASE_URL}/api/skilled/", timeout=30)
        resp.raise_for_status()
        data = resp.json()
        logging.debug(f"GET /api/skilled/ -> {data}")
        return {"status": "success", "report": data}
    except requests.exceptions.Timeout:
        return {"status": "error", "report": "The request timed out. Please try again later."}
    except requests.exceptions.RequestException as e:
        return {"status": "error", "report": f"An error occurred: {str(e)}"}

def get_skills(query: str = "") -> dict:
    try:
        resp = requests.get(f"{BASE_URL}/api/skills/", timeout=30)
        resp.raise_for_status()
        data = resp.json()
        logging.debug(f"GET /api/skills/ -> {data}")
        return {"status": "success", "report": data}
    except requests.exceptions.Timeout:
        return {"status": "error", "report": "The request timed out. Please try again later."}
    except requests.exceptions.RequestException as e:
        return {"status": "error", "report": f"An error occurred: {str(e)}"}

def get_work(query: str = "") -> dict:
    try:
        resp = requests.get(f"{BASE_URL}/api/work/", timeout=30)
        resp.raise_for_status()
        data = resp.json()
        logging.debug(f"GET /api/work/ -> {data}")
        return {"status": "success", "report": data}
    except requests.exceptions.Timeout:
        return {"status": "error", "report": "The request timed out. Please try again later."}
    except requests.exceptions.RequestException as e:
        return {"status": "error", "report": f"An error occurred: {str(e)}"}
