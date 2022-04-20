from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('<str:contract_address>/', views.factory_contract_summary, name='factory_contract_summary'),
]