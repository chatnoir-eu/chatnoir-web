from django.db import migrations, models


def create_web_frontend_key(apps, schema_editor):
    ApiConfiguration = apps.get_model('chatnoir_api', 'ApiConfiguration')
    ApiKey = apps.get_model('chatnoir_api', 'ApiKey')

    config = ApiConfiguration.objects.get()
    root_key = config.default_issue_key
    while root_key.parent_id:
        root_key = root_key.parent

    web_frontend_key, _ = ApiKey.objects.get_or_create(
        comments='WEB FRONTEND',
        defaults={
            'user': root_key.user,
            'parent': root_key,
            'issuer': 'web_frontend',
        }
    )

    config.web_frontend_key = web_frontend_key
    config.save(update_fields=['web_frontend_key'])


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ('chatnoir_api', '0005_apikey_keyid_private_key'),
    ]

    operations = [
        migrations.AddField(
            model_name='apiconfiguration',
            name='web_frontend_key',
            field=models.ForeignKey(
                blank=True,
                help_text='Default key for anonymous web frontend token issuance',
                null=True,
                on_delete=models.deletion.CASCADE,
                related_name='+',
                to='chatnoir_api.apikey',
                verbose_name='Web Frontend API Key',
            ),
        ),
        migrations.RunPython(create_web_frontend_key, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='apiconfiguration',
            name='web_frontend_key',
            field=models.ForeignKey(
                help_text='Default key for anonymous web frontend token issuance',
                on_delete=models.deletion.CASCADE,
                related_name='+',
                to='chatnoir_api.apikey',
                verbose_name='Web Frontend API Key',
            ),
        ),
    ]
