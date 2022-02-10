# Copyright 2021 Janek Bevendorff
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

from django.conf import settings
from django.contrib import admin, messages
from django.db.models import Q
from django.forms import ModelForm, TextInput
from django.utils.translation import gettext_lazy as _, ngettext

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
    list_display = ('api_key', 'roles_str', 'expires_inherited', 'is_valid', 'user', 'comment')
    list_filter = ('roles', 'user', 'expires')

    def is_valid(self, obj):
        return obj.is_valid

    is_valid.boolean = True
    is_valid.short_description = _('Valid')

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)

        # Exclude keys which are not allowed to issue other API keys
        if '/autocomplete/' in request.path:
            queryset = queryset.filter(Q(roles__in=_keycreate_roles) &
                                       (Q(expires__gte=timezone.now()) | Q(expires__isnull=True)))

            # Prevent cycles through self-parenting
            if request.META.get('HTTP_REFERER') and '/apikey/' in request.META.get('HTTP_REFERER'):
                p = os.path.basename(os.path.dirname(request.META.get('HTTP_REFERER').rstrip('/')))
                queryset = queryset.exclude(api_key=p)

            queryset = [r for r in queryset if self.is_valid(r)]

        return queryset, use_distinct


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
    list_display = ('common_name', 'passcode', 'email', 'organization', 'address', 'zip_code', 'state',
                    'country', 'email_verified')
    list_filter = ('organization', 'zip_code', 'state', 'country', 'email_verified')
    search_fields = ('common_name', 'passcode__passcode', 'email', 'organization', 'address',
                     'zip_code', 'state', 'country')
    autocomplete_fields = ('passcode', 'issue_key')
    actions = ['activate_pending_user', 'activate_pending_user_and_send_mail']

    @admin.action(description=_('Activate selected API Users'))
    def activate_pending_user(self, request, queryset, send_emails=False):
        successful = 0
        for user in queryset:
            if not user.issue_key and not user.passcode:
                self.message_user(request, _('User "%s" failed to activate: No parent key or passcode set.')
                                  % user.common_name, messages.ERROR)
                continue
            user.activate(send_emails)
            successful += 1

        if successful > 0:
            self.message_user(request, ngettext('%s user successfully activated.',
                                                '%s users successfully activated.',
                                                successful) % successful, messages.SUCCESS)

    @admin.action(description=_('Activate selected API Users and notify by email'))
    def activate_pending_user_and_send_mail(self, request, queryset):
        self.activate_pending_user(request, queryset, send_emails=True)


class ApiKeyRoleAdmin(admin.ModelAdmin):
    list_display = ('role',)
    search_fields = list_display


class ApiKeyPasscodeAdmin(admin.ModelAdmin):
    list_display = ('passcode', 'expires')
    search_fields = list_display
    autocomplete_fields = ('issue_key',)


class ApiKeyPasscodeRedemptionAdmin(admin.ModelAdmin):
    list_display = ('api_key', 'redemption_date', 'passcode')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


admin.site.register(ApiKey, ApiKeyAdmin)
admin.site.register(ApiUser, ApiUserAdmin)
admin.site.register(ApiKeyRole, ApiKeyRoleAdmin)
admin.site.register(ApiKeyPasscode, ApiKeyPasscodeAdmin)
admin.site.register(PasscodeRedemption, ApiKeyPasscodeRedemptionAdmin)
admin.site.register(PendingApiUser, PendingApiUserAdmin)
