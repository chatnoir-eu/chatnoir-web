from django.conf import settings
from django.contrib import admin
from django.db.models import F, Q

from .models import *


_keycreate_roles = (settings.API_ADMIN_ROLE, settings.API_KEY_CREATE_ROLE)


class ApiKeyAdmin(admin.ModelAdmin):
    list_display = ('api_key', 'parent_str', 'roles_str', 'expires', 'user')
    list_filter = ('parent', 'roles', 'user', 'expires')
    search_fields = ('api_key', 'parent__api_key', 'roles__role', 'user__common_name', 'user__email')
    autocomplete_fields = ('parent', 'user')

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)

        # Exclude keys which are not allowed to issue other API keys
        if 'apikey/autocomplete/' in request.path:
            queryset = queryset.filter(roles__in=_keycreate_roles)

        return queryset, use_distinct


class ApiUserAdmin(admin.ModelAdmin):
    list_display = ('common_name', 'api_keys_plain', 'email', 'organization', 'address', 'zip_code', 'state', 'country')
    list_filter = ('common_name', 'api_key', 'email', 'organization', 'address', 'zip_code', 'state', 'country')
    search_fields = ('common_name', 'api_key__api_key', 'email', 'organization', 'address',
                     'zip_code', 'state', 'country')


class PendingApiUserAdmin(admin.ModelAdmin):
    list_display = ('common_name', 'passcode', 'email', 'organization', 'address', 'zip_code', 'state', 'country')
    list_filter = list_display
    search_fields = ('common_name', 'passcode__passcode', 'email', 'organization', 'address',
                     'zip_code', 'state', 'country')
    autocomplete_fields = ('passcode',)


class ApiKeyRoleAdmin(admin.ModelAdmin):
    list_display = ('role',)
    search_fields = list_display


class ApiKeyPasscodeAdmin(admin.ModelAdmin):
    list_display = ('passcode', 'expires')
    search_fields = list_display
    autocomplete_fields = ('issue_key',)


admin.site.register(ApiKey, ApiKeyAdmin)
admin.site.register(ApiUser, ApiUserAdmin)
admin.site.register(ApiKeyRole, ApiKeyRoleAdmin)
admin.site.register(ApiKeyPasscode, ApiKeyPasscodeAdmin)
admin.site.register(PendingApiUser, PendingApiUserAdmin)
