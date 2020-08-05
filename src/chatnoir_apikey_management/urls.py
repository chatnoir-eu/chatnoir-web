from django.contrib import admin
from django.urls import path

from . import views

app_name = 'apikey_management'

urlpatterns = [
    path('', views.index, name='index'),
    path('apikey/admin/', admin.site.urls, name='admin'),
    path('activate/<slug:activation_code>', views.activate, name='activate'),
    path('request_sent', views.request_sent, name='request_sent')
]
