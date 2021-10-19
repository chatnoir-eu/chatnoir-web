from django.urls import include, path, reverse_lazy
from django.contrib import admin
from django.views.generic import RedirectView

app_name = 'chatnoir'

urlpatterns = [
    path(r'', include('chatnoir_web.urls')),
    path(r'api/', RedirectView.as_view(url=reverse_lazy('api_v1:api-root'))),
    path(r'api/v1/', include('chatnoir_api_v1.urls')),
    path(r'apikey/', include('chatnoir_apikey_management.urls')),
    path(r'apikey/admin/', admin.site.urls),
]
