from django.urls import include, path

app_name = 'main'

urlpatterns = [
    path(r'', include('sigir21_chatonir_web.urls')),
]
