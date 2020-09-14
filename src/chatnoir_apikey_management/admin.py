from datetime import date
import os

from django.conf import settings
from django.contrib import admin
from django.db.models import Q
from django.forms import ModelForm, TextInput
from django.utils.translation import gettext_lazy as _

from .models import *


_keycreate_roles = (settings.API_ADMIN_ROLE, settings.API_KEY_CREATE_ROLE)


class ApiKeyAdminBase:
    autocomplete_fields = ('parent', 'user', 'roles')
    search_fields = ('api_key', 'parent__api_key', 'roles__role', 'user__common_name', 'user__email', 'comment')
    formfield_overrides = {
        models.TextField: {'widget': TextInput(attrs={'class': 'vTextField'})}
    }
    fields = (
        ('api_key', 'revoked'),
        'user',
        'parent',
        ('issue_date', 'expires'),
        ('limits_day', 'limits_week', 'limits_month'),
        'roles',
        'allowed_remote_hosts',
        'comment'
    )


class ApiKeyAdmin(ApiKeyAdminBase, admin.ModelAdmin):
    list_display = ('api_key', 'roles_str', 'expires_inherited', 'is_revoked', 'user', 'comment')
    list_filter = ('roles', 'user', 'expires')

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)

        # Exclude keys which are not allowed to issue other API keys
        if 'apikey/autocomplete/' in request.path:
            queryset = queryset.filter(Q(roles__in=_keycreate_roles) &
                                       (Q(expires__gte=date.today()) | Q(expires__isnull=True)))

            # Prevent cycles through self-parenting
            if request.META.get('HTTP_REFERER') and '/apikey/' in request.META.get('HTTP_REFERER'):
                p = os.path.basename(os.path.dirname(request.META.get('HTTP_REFERER').rstrip('/')))
                queryset = queryset.exclude(api_key=p)

            results = []
            for r in queryset:
                expires = r.resolve_inheritance('expires')
                if not expires or expires >= date.today():
                    results.append(r)
            queryset = results

        return queryset, use_distinct

    def is_revoked(self, obj):
        return obj.is_revoked

    is_revoked.short_description = _('Revoked')
    is_revoked.boolean = True


class AlwaysChangedModelForm(ModelForm):
    def has_changed(self):
        return True


class ApiKeyInlineAdmin(ApiKeyAdminBase, admin.StackedInline):
    model = ApiKey
    extra = 0
    form = AlwaysChangedModelForm


class ApiUserAdmin(admin.ModelAdmin):
    list_display = ('common_name', 'api_keys_html', 'email', 'organization', 'address', 'zip_code', 'state', 'country')
    list_filter = ('organization', 'zip_code', 'state', 'country')
    search_fields = ('common_name', 'api_key__api_key', 'email', 'organization', 'address',
                     'zip_code', 'state', 'country')
    inlines = (ApiKeyInlineAdmin,)


class PendingApiUserAdmin(admin.ModelAdmin):
    list_display = ('common_name', 'passcode', 'email', 'organization', 'address', 'zip_code', 'state', 'country')
    list_filter = ('organization', 'zip_code', 'state', 'country')
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
