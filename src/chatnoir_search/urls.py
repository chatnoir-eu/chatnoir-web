from django.urls import path

from . import views

app_name = 'search'

urlpatterns = [
    path(r'', views.index, name='index'),
    path(r'cache', views.cache, name='cache')
]
