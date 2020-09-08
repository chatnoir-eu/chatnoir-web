# from rest_framework_api_key.permissions import HasAPIKey, KeyParser
#
#
# class KeyParserV1(KeyParser):
#     def get(self, request):
#         if 'apikey' in request.data:
#             return request.data['apikey']
#         if 'apikey' in request.GET:
#             print(request.GET)
#             return request.GET['apikey']
#         return super().get(request)
#
#
# class HasAPIKeyV1(HasAPIKey):
#     key_parser = KeyParserV1()
#
#     # def has_permission(self, request, view):
#     #     return True

from rest_framework import permissions
from chatnoir_apikey_management.models import ApiKey

# class OnlyAPIPermission(permissions.BasePermission):
#     def has_permission(self, request, view):
#         try:
#             api_key = request.QUERY_PARAMS.get('apikey', False)
#             RestApiKey.objects.get(api_key=api_key)
#             return True
#         except:
#             return False
