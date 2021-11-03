from django.urls import path

from . import views

app_name = 'chatnoir_apikey_management'

urlpatterns = [
    path(r'', views.index, name='index'),
    path(r'activate/<slug:activation_code>', views.activate, name='activate'),
    path(r'request_sent', views.request_sent, name='request_sent')
]
