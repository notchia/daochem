from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('factories', views.factories, name='factories'),
    path('twitter', views.twitter, name='twitter'),
    path('sentiment', views.sentiment, name='sentiment'),
    path('about', views.about, name='about'),
]