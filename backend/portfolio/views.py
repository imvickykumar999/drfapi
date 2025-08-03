from django.shortcuts import render, redirect
from django.contrib import messages
from .models import *
import requests

TELEGRAM_BOT_TOKEN = 'TELEGRAM_BOT_TOKEN'
TELEGRAM_CHAT_ID = 'TELEGRAM_CHAT_ID'

def send_telegram_message(name, email, message):
    text = f"📬 New Portfolio Message:\n\n👤 Name: {name}\n📧 Email: {email}\n\n📝 Message:\n{message}"
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': text,
        'parse_mode': 'Markdown'
    }
    try:
        requests.post(url, data=payload, timeout=5)
    except requests.exceptions.RequestException:
        pass  # You can log this if needed

def index(request):
    home_content = Home.objects.first()
    about_content = About.objects.first()
    skills = Skill.objects.all()
    skilled = Skilled.objects.first()
    works = Work.objects.all()

    if request.method == 'POST':
        name = request.POST.get('flname')
        email = request.POST.get('email')
        message = request.POST.get('message')

        if name and email and message:
            Contact.objects.create(name=name, email=email, message=message)
            send_telegram_message(name, email, message)
            messages.success(request, 'Your message has been sent successfully!')
            return redirect('index')

    return render(request, 'portfolio/index.html', {
        'home_content': home_content,
        'about_content': about_content,
        'skills': skills,
        'skilled': skilled,
        'works': works,
    })
