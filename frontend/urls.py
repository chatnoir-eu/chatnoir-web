from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('request_sent', views.request_sent, name='request_sent'),
    path('activate/<slug:activation_code>', views.activate, name='activate')
]
