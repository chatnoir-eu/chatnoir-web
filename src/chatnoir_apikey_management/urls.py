from django.contrib import admin
from django.urls import path

from . import views

app_name = 'apikey_management'

urlpatterns = [
    path(r'', views.index, name='index'),
    path(r'apikey/admin/', admin.site.urls, name='admin'),
    path(r'activate/<slug:activation_code>', views.activate, name='activate'),
    path(r'request_sent', views.request_sent, name='request_sent')
]
