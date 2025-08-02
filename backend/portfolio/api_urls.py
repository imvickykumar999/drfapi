from django.urls import path
from . import api_views

urlpatterns = [
    path('home/', api_views.HomeView.as_view(), name='home-api'),
    path('about/', api_views.AboutView.as_view(), name='about-api'),
    path('skilled/', api_views.SkilledView.as_view(), name='skilled-api'),
    path('skills/', api_views.SkillView.as_view(), name='skills-api'),
    path('work/', api_views.WorkView.as_view(), name='work-api'),
]
