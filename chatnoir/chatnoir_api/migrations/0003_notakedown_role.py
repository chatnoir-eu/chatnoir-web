from django.db import migrations, transaction
from django.utils.translation import gettext as _


def create_notakedown_role(apps, schema_editor):
    with transaction.atomic():
        ApiKeyRole = apps.get_model('chatnoir_api', 'ApiKeyRole')
        ApiKeyRole.objects.get_or_create(
            role='notakedown',
            defaults={'description': _('Key allowed to access taken-down documents')},
        )


def remove_notakedown_role(apps, schema_editor):
    with transaction.atomic():
        ApiKeyRole = apps.get_model('chatnoir_api', 'ApiKeyRole')
        ApiKeyRole.objects.filter(role='notakedown').delete()


class Migration(migrations.Migration):
    dependencies = [
        ('chatnoir_api', '0002_initial_data'),
    ]

    operations = [
        migrations.RunPython(create_notakedown_role, remove_notakedown_role),
    ]
