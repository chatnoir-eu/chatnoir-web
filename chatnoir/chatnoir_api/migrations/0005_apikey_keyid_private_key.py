import chatnoir_api.models
from django.db import migrations, models

def populate_apikey_fields(apps, _):
    ApiKey = apps.get_model('chatnoir_api', 'ApiKey')

    existing_ids = set(ApiKey.objects.exclude(key_id__isnull=True).exclude(key_id='').values_list('key_id', flat=True))

    for api_key in ApiKey.objects.all():
        changed = False

        if not api_key.key_id:
            key_id = chatnoir_api.models.generate_apikey_id()
            while key_id in existing_ids:
                key_id = chatnoir_api.models.generate_apikey_id()
            api_key.key_id = key_id
            existing_ids.add(key_id)
            changed = True

        if not api_key.private_key:
            api_key.private_key = chatnoir_api.models.generate_private_key()
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
