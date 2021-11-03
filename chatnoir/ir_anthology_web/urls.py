from django.urls import path

from . import views

app_name = 'ir_anthology_web'

urlpatterns = [
    path(r'', views.index, name='index'),
    path(r'search', views.search, name='search')
]
