# api_views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Home, About, Skilled, Skill, Work, Contact
from .serializers import HomeSerializer, AboutSerializer, SkilledSerializer, SkillSerializer, WorkSerializer
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .views import send_telegram_message
from django.shortcuts import render
from django.urls import get_resolver

class HomeView(APIView):
    def get(self, request):
        home_content = Home.objects.first()
        serializer = HomeSerializer(home_content, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

class AboutView(APIView):
    def get(self, request):
        about_content = About.objects.first()
        serializer = AboutSerializer(about_content, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

class SkilledView(APIView):
    def get(self, request):
        skilled_content = Skilled.objects.first()
        serializer = SkilledSerializer(skilled_content, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

class SkillView(APIView):
    def get(self, request):
        skills = Skill.objects.all()
        serializer = SkillSerializer(skills, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

class WorkView(APIView):
    def get(self, request):
        works = Work.objects.all()
        serializer = WorkSerializer(works, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

@csrf_exempt
def submit_contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')

        if name and email and message:
            Contact.objects.create(name=name, email=email, message=message)
            send_telegram_message(name, email, message)
            return JsonResponse({"message": "Your message has been sent successfully!"}, status=200)
        else:
            return JsonResponse({"error": "Please fill in all the fields."}, status=400)
    return JsonResponse({"error": "Invalid request method."}, status=405)

def api_overview(request):
    api_routes = []
    for pattern in get_resolver().url_patterns:
        if hasattr(pattern, 'url_patterns'):
            if pattern.pattern._route == 'api/':
                for sub_pattern in pattern.url_patterns:
                    name = sub_pattern.name or 'No Name'
                    url = f"/api/{sub_pattern.pattern._route}"
                    api_routes.append((name, url))
    return render(request, 'api_overview.html', {'routes': api_routes})
