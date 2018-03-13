from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('request_key/', views.request_key, name='request_key')
]
