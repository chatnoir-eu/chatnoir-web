from django.urls import include, path, reverse_lazy
from django.views.generic import RedirectView
from rest_framework import routers

from . import views

app_name = 'api'

router_v1 = routers.DefaultRouter(trailing_slash=False)
router_v1.APIRootView = views.APIRootV1
router_v1.register(r'_search', views.SimpleSearchViewSetV1, basename='v1-search')
router_v1.register(r'_phrases', views.PhraseSearchViewSetV1, basename='v1-phrases')

urlpatterns = [
    path(r'', RedirectView.as_view(url=reverse_lazy('api:api-root'))),
    path(r'v1/', include(router_v1.urls))
]
