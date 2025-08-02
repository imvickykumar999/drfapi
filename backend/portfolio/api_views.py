# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Home, About, Skilled, Skill, Work
from .serializers import HomeSerializer, AboutSerializer, SkilledSerializer, SkillSerializer, WorkSerializer

class HomeView(APIView):
    def get(self, request):
        home_content = Home.objects.first()
        serializer = HomeSerializer(home_content)
        return Response(serializer.data, status=status.HTTP_200_OK)

class AboutView(APIView):
    def get(self, request):
        about_content = About.objects.first()
        serializer = AboutSerializer(about_content)
        return Response(serializer.data, status=status.HTTP_200_OK)

class SkilledView(APIView):
    def get(self, request):
        skilled_content = Skilled.objects.first()
        serializer = SkilledSerializer(skilled_content)
        return Response(serializer.data, status=status.HTTP_200_OK)

class SkillView(APIView):
    def get(self, request):
        skills = Skill.objects.all()
        serializer = SkillSerializer(skills, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class WorkView(APIView):
    def get(self, request):
        works = Work.objects.all()
        serializer = WorkSerializer(works, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
