from django.urls import path, re_path

from . import views

app_name = 'search'

urlpatterns = [
    path(r'', views.index, name='index'),
    path(r'cache', views.cache, name='cache'),
    path(r'doc/', views.doc, name='doc'),
    re_path(r'doc/(?P<subpath>.+)/$', views.doc, name='doc-sub')
]
