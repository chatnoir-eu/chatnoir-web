from django.conf import settings
from django.core.management import call_command
from django.db import migrations, transaction
from django.utils.translation import gettext as _


# noinspection PyPep8Naming
def init_root_api_key(apps, schema_editor):
    with transaction.atomic():
        ApiKeyRole = apps.get_model('chatnoir_api_v1', 'ApiKeyRole')
        admin_role = ApiKeyRole(role=settings.API_ADMIN_ROLE)
        admin_role.save()
        ApiKeyRole(role=settings.API_KEY_CREATE_ROLE).save()
        for role in settings.API_NOLOG_ROLES:
            ApiKeyRole(role=role).save()

        # Root user
        ApiUser = apps.get_model('chatnoir_api_v1', 'ApiUser')
        api_user = ApiUser(common_name=_('ROOT'), email='root@localhost')
        api_user.save()

        # API root key
        ApiKey = apps.get_model('chatnoir_api_v1', 'ApiKey')
        root_key = ApiKey(user=api_user,
                          allowed_remote_hosts='127.0.0.1,::1',
                          comment=_('ROOT KEY'))
        root_key.save()
        root_key.roles.add(admin_role)

        # Default issue key
        default_limit = 10000
        keycreate_role = ApiKeyRole(role=settings.API_KEY_CREATE_ROLE)
        keycreate_role.save()
        default_key = ApiKey(user=api_user,
                             allowed_remote_hosts='127.0.0.1,::1',
                             parent=root_key,
                             limits_day=default_limit,
                             limits_week=default_limit * 7,
                             limits_month=default_limit * 30,
                             comment=_('DEFAULT ISSUE KEY'))
        default_key.save()
        default_key.roles.add(admin_role)


def create_cache_table(apps, schema_editor):
    call_command('createcachetable')


class Migration(migrations.Migration):
    dependencies = [
        ('chatnoir_api_v1', '0001_initial')
    ]

    operations = [
        migrations.RunPython(create_cache_table),
        migrations.RunPython(init_root_api_key)
    ]
