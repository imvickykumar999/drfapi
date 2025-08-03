from rest_framework import serializers
from .models import Home, About, Skilled, Skill, Work, Contact

class HomeSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Home
        fields = '__all__'

    def get_image(self, obj):
        request = self.context.get('request')
        if request is not None:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url

class AboutSerializer(serializers.ModelSerializer):
    profile_image = serializers.SerializerMethodField()

    class Meta:
        model = About
        fields = '__all__'

    def get_profile_image(self, obj):
        request = self.context.get('request')
        if obj.profile_image and request:
            return request.build_absolute_uri(obj.profile_image.url)
        return obj.profile_image.url if obj.profile_image else None

class SkilledSerializer(serializers.ModelSerializer):
    profile_image = serializers.SerializerMethodField()

    class Meta:
        model = Skilled
        fields = '__all__'

    def get_profile_image(self, obj):
        request = self.context.get('request')
        if obj.profile_image and request:
            return request.build_absolute_uri(obj.profile_image.url)
        return obj.profile_image.url if obj.profile_image else None

class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = '__all__'

class WorkSerializer(serializers.ModelSerializer):
    project_image = serializers.SerializerMethodField()

    class Meta:
        model = Work
        fields = '__all__'

    def get_project_image(self, obj):
        request = self.context.get('request')
        if obj.project_image and request:
            return request.build_absolute_uri(obj.project_image.url)
        return obj.project_image.url if obj.project_image else None

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = '__all__'
