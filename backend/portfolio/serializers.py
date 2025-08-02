from rest_framework import serializers
from .models import Home, About, Skilled, Skill, Work, Contact

class HomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Home
        fields = '__all__'

class AboutSerializer(serializers.ModelSerializer):
    class Meta:
        model = About
        fields = '__all__'

class SkilledSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skilled
        fields = '__all__'

class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = '__all__'

class WorkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Work
        fields = '__all__'

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = '__all__'
