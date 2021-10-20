from django.urls import path

from . import views

app_name = 'chatnoir_web'

urlpatterns = [
    path(r'', views.index, name='index')
]
