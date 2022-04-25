from django.urls import path

from . import views

urlpatterns = [
    path('', views.index_test, name='index'),
#   path('factories', views.factories, name='factories'),
]