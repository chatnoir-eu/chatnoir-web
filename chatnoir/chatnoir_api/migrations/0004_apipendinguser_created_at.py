from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ('chatnoir_api', '0003_notakedown_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='apipendinguser',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='Created at'),
        ),
    ]
