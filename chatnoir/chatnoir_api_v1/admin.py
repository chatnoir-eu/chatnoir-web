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

from django.contrib import admin, messages
from django.db.models import Q
from django.forms import ModelForm, Textarea
from django.utils.translation import gettext_lazy as _, ngettext
from solo.admin import SingletonModelAdmin

from .models import *
from .forms import PendingApiUserAdminForm


# Textareas are way too large
admin.ModelAdmin.formfield_overrides = {
    models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 60})},
}
admin.StackedInline.formfield_overrides = {
    models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 60})},
}


class ApiKeyAdminBaseMixin:
    autocomplete_fields = ('parent', 'user', 'roles')
    search_fields = ('api_key', 'parent__api_key', 'roles__role', 'user__common_name', 'user__email', 'comments')
    fields = (
        ('api_key', '_revoked'),
        'user',
        'parent',
        ('issue_date', '_expires'),
        ('_limits_day', '_limits_week', '_limits_month'),
        'roles',
        'allowed_remote_hosts',
        'comments',
        'issuer',
    )
    readonly_fields = ('issuer',)


class ApiKeyAdmin(ApiKeyAdminBaseMixin, admin.ModelAdmin):
    list_display = ('api_key', 'roles_str', 'expires', '_valid_bool', 'user', 'comments')
    list_filter = ('roles', )
    readonly_fields = ApiKeyAdminBaseMixin.readonly_fields + (
        '_valid_bool',
        'expires',
        '_has_expired_bool',
        '_revoked_bool',
        'limits_day',
        'limits_week',
        'limits_month',
    )
    actions = ('revoke_keys', 'unrevoke_keys')

    # Django ignores `boolean` attribute of computed properties
    def _valid_bool(self, obj):
        return obj.valid

    _valid_bool.boolean = True
    _valid_bool.short_description = ApiKey.valid.fget.short_description

    def _revoked_bool(self, obj):
        return obj.revoked

    _revoked_bool.boolean = True
    _revoked_bool.short_description = ApiKey.revoked.fget.short_description

    def _has_expired_bool(self, obj):
        return obj.has_expired

    _has_expired_bool.boolean = True
    _has_expired_bool.short_description = ApiKey.has_expired.fget.short_description

    def get_fieldsets(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if obj is not None:
            # Add inherited properties if model instance exists
            return (
                (_('Key Details'), {'fields': fields}),
                (_('Inherited Properties'), {'fields': (
                    'expires',
                    '_has_expired_bool',
                    '_revoked_bool',
                    '_valid_bool',
                    ('limits_day', 'limits_week', 'limits_month'),
                )})
            )

        return (None, {'fields': fields}),

    def get_fields(self, request, obj=None):
        return None

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)

        # Exclude keys which are not allowed to issue other API keys
        if '/autocomplete/' in request.path:
            keycreate_roles = (settings.API_ADMIN_ROLE, settings.API_KEYCREATE_ROLE)
            queryset = queryset.filter(Q(roles__in=keycreate_roles, _revoked=False),
                                       Q(_expires__gte=timezone.now()) | Q(_expires__isnull=True))

            # Prevent cycles through self-parenting
            if request.META.get('HTTP_REFERER') and '/apikey/' in request.META.get('HTTP_REFERER'):
                p = os.path.basename(os.path.dirname(request.META.get('HTTP_REFERER').rstrip('/')))
                queryset = queryset.exclude(api_key=p)

            queryset = [r for r in queryset if r.valid]

        return queryset, use_distinct

    @admin.action(description=_('Revoke selected API Keys'))
    def revoke_keys(self, request, queryset):
        count = 0
        for key in queryset:
            key._revoked = True
            count += 1
        ApiKey.objects.bulk_update(queryset, ['_revoked'])

        if count > 0:
            self.message_user(request, ngettext('%s API key successfully revoked.',
                                                '%s API keys successfully revoked.',
                                                count) % count, messages.SUCCESS)

    @admin.action(description=_('Unrevoke selected API Keys'))
    def unrevoke_keys(self, request, queryset):
        count = 0
        for key in queryset:
            key._revoked = False
            count += 1
        ApiKey.objects.bulk_update(queryset, ['_revoked'])

        if count > 0:
            self.message_user(request, ngettext('%s API key successfully unrevoked.',
                                                '%s API keys successfully unrevoked.',
                                                count) % count, messages.SUCCESS)


class AlwaysChangedModelForm(ModelForm):
    def has_changed(self):
        return True


class ApiKeyInlineAdmin(ApiKeyAdminBaseMixin, admin.StackedInline):
    model = ApiKey
    extra = 0
    form = AlwaysChangedModelForm


class ApiUserAdmin(admin.ModelAdmin):
    list_display = ('common_name', 'api_keys_html', 'email', 'organization', 'address', 'zip_code', 'state', 'country')
    list_filter = ('organization', 'zip_code', 'state', 'country')
    search_fields = ('common_name', 'api_key__api_key', 'email', 'organization', 'address',
                     'zip_code', 'state', 'country')
    inlines = (ApiKeyInlineAdmin,)


class ApiPendingUserAdmin(admin.ModelAdmin):
    list_display = ('common_name', 'passcode', 'email', 'organization', 'address', 'zip_code', 'state',
                    'country', 'email_verified', 'user_exists')
    list_filter = ('organization', 'zip_code', 'state', 'country', 'email_verified')
    search_fields = ('common_name', 'passcode__passcode', 'email', 'organization', 'address',
                     'zip_code', 'state', 'country')
    autocomplete_fields = ('passcode', 'issue_key')
    actions = ['activate_pending_user', 'activate_pending_user_and_send_mail']

    form = PendingApiUserAdminForm
    fieldsets = (
        (_('User details:'), {'fields': (
            'common_name',
            'email',
            'email_verified',
            'user_exists',
            'issue_key',
            'passcode',
            'organization',
            'address',
            'zip_code',
            'state',
            'country',
            'comments')
        }),
        (_('Approve or deny API key request:'), {
            'fields': (
                'activate_user',
                ('deny_request', 'confirm_denial'))
        })
    )
    readonly_fields = ['email_verified', 'user_exists']

    @admin.action(description=_('Activate selected API Users and notify by email'))
    def activate_pending_user(self, request, queryset):
        successful = 0
        for user in queryset:
            if not user.issue_key and not user.passcode:
                self.message_user(request, _('User "%s" failed to activate: No parent key or passcode set.')
                                  % user.common_name, messages.ERROR)
                continue
            user.activate(send_email=True)
            successful += 1

        if successful > 0:
            self.message_user(request, ngettext('%s user successfully activated.',
                                                '%s users successfully activated.',
                                                successful) % successful, messages.SUCCESS)

    def save_model(self, request, obj, form, change):
        if change:
            if form.cleaned_data.get('activate_user'):
                obj.activate(send_email=True)
                return

            deny_reason = form.cleaned_data.get('deny_request')
            if deny_reason:
                if deny_reason == 'academic-status':
                    deny_reason = _('We could not verify your academic status. If you are indeed affiliated with '
                                    'an academic institute, please re-apply with more information. You are also '
                                    'welcome to apply again whenever your academic status changes.')
                elif deny_reason == 'already-issued':
                    deny_reason = _('An API key has already been issued to this user. If you lost your key and need '
                                    'a new one please contact us directly.')
                elif deny_reason == 'applications-suspended':
                    deny_reason = _('We are not accepting new applications at the time. Please apply again later.')
                else:
                    deny_reason = 'No reason given'

                obj.delete(email_reason=deny_reason)
                return

        super().save_model(request, obj, form, change)


class ApiKeyRoleAdmin(admin.ModelAdmin):
    list_display = ('role', 'description')
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


admin.site.register(ApiConfiguration, SingletonModelAdmin)
admin.site.register(ApiKey, ApiKeyAdmin)
admin.site.register(ApiUser, ApiUserAdmin)
admin.site.register(ApiKeyRole, ApiKeyRoleAdmin)
admin.site.register(ApiKeyPasscode, ApiKeyPasscodeAdmin)
admin.site.register(PasscodeRedemption, ApiKeyPasscodeRedemptionAdmin)
admin.site.register(ApiPendingUser, ApiPendingUserAdmin)
