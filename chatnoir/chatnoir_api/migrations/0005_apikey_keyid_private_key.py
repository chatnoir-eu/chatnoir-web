from django.db import migrations, models
from django.utils.crypto import get_random_string
import chatnoir_api.models


ALLOWED_CHARS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'


def _random_token(size=32):
    return get_random_string(size, allowed_chars=ALLOWED_CHARS)


def populate_apikey_fields(apps, schema_editor):
    ApiKey = apps.get_model('chatnoir_api', 'ApiKey')

    existing_ids = set(ApiKey.objects.exclude(key_id__isnull=True).exclude(key_id='').values_list('key_id', flat=True))

    for api_key in ApiKey.objects.all():
        changed = False

        if not api_key.key_id:
            key_id = _random_token()
            while key_id in existing_ids:
                key_id = _random_token(16)
            api_key.key_id = key_id
            existing_ids.add(key_id)
            changed = True

        if not api_key.private_key:
            api_key.private_key = _random_token()
            changed = True

        if changed:
            api_key.save(update_fields=['key_id', 'private_key'])


class Migration(migrations.Migration):

    dependencies = [
        ('chatnoir_api', '0004_apipendinguser_created_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='apikey',
            name='key_id',
            field=models.CharField(blank=True, default='', max_length=255, verbose_name='API Key ID'),
        ),
        migrations.AddField(
            model_name='apikey',
            name='private_key',
            field=models.CharField(blank=True, default='', max_length=255, verbose_name='Private Key'),
        ),
        migrations.RunPython(populate_apikey_fields, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='apikey',
            name='key_id',
            field=models.CharField(default=chatnoir_api.models.generate_apikey_id, max_length=255, unique=True,
                                   verbose_name='API Key ID'),
        ),
        migrations.AlterField(
            model_name='apikey',
            name='private_key',
            field=models.CharField(default=chatnoir_api.models.generate_private_key, max_length=255,
                                   verbose_name='Private Key'),
        ),
    ]
