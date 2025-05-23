# Generated by Django 4.1.3 on 2022-12-05 16:11

import chatnoir_api.models
from django.db import migrations, models
import django.utils.timezone
import django_countries.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ApiKey',
            fields=[
                ('api_key', models.CharField(default=chatnoir_api.models.generate_apikey, max_length=255, primary_key=True, serialize=False, verbose_name='API Key')),
                ('issue_date', models.DateTimeField(blank=True, default=django.utils.timezone.now, null=True, verbose_name='Issue Date')),
                ('issuer', models.CharField(blank=True, default='manual', max_length=64, verbose_name='API Key Issuer')),
                ('allowed_remote_hosts', models.TextField(blank=True, null=True, verbose_name='Allowed Remote Hosts')),
                ('comments', models.TextField(blank=True, verbose_name='Comments')),
                ('quota_used', models.BinaryField(blank=True, default=b'')),
                ('_expires', models.DateTimeField(blank=True, db_column='expires', null=True, verbose_name='Expiration Date')),
                ('_revoked', models.BooleanField(blank=True, db_column='revoked', default=False, verbose_name='Revoked')),
                ('_limits_day', models.PositiveIntegerField(blank=True, db_column='limits_day', null=True, verbose_name='Request Limit Day')),
                ('_limits_week', models.PositiveIntegerField(blank=True, db_column='limits_week', null=True, verbose_name='Request Limit Week')),
                ('_limits_month', models.PositiveIntegerField(blank=True, db_column='limits_month', null=True, verbose_name='Request Limit Month')),
                ('_is_root_key', models.BooleanField(default=False, verbose_name='Root API Key')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='chatnoir_api.apikey', verbose_name='Parent Key')),
            ],
            options={
                'verbose_name': 'API Key',
                'verbose_name_plural': 'API Keys',
            },
        ),
        migrations.CreateModel(
            name='ApiKeyPasscode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('passcode', models.CharField(max_length=100, unique=True, verbose_name='Passcode')),
                ('expires', models.DateField(blank=True, null=True, verbose_name='Expiration Date')),
                ('issue_key', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='chatnoir_api.apikey', verbose_name='Issue Key')),
            ],
            options={
                'verbose_name': 'Passcode',
                'verbose_name_plural': 'Passcodes',
            },
        ),
        migrations.CreateModel(
            name='ApiKeyRole',
            fields=[
                ('role', models.CharField(max_length=255, primary_key=True, serialize=False, verbose_name='API Key Role')),
                ('description', models.CharField(blank=True, max_length=512, verbose_name='Description')),
            ],
            options={
                'verbose_name': 'API Key Role',
                'verbose_name_plural': 'API Key Roles',
            },
        ),
        migrations.CreateModel(
            name='ApiUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('common_name', models.CharField(max_length=100, verbose_name='Common Name')),
                ('email', models.EmailField(max_length=200, unique=True, verbose_name='Email Address')),
                ('organization', models.CharField(blank=True, max_length=100, null=True, verbose_name='Organization')),
                ('address', models.CharField(blank=True, max_length=200, null=True, verbose_name='Address')),
                ('zip_code', models.CharField(blank=True, max_length=50, null=True, verbose_name='ZIP Code')),
                ('state', models.CharField(blank=True, max_length=50, null=True, verbose_name='State')),
                ('country', django_countries.fields.CountryField(blank=True, max_length=50, null=True, verbose_name='Country')),
            ],
            options={
                'verbose_name': 'User',
                'verbose_name_plural': 'Users',
            },
        ),
        migrations.AddField(
            model_name='apikey',
            name='roles',
            field=models.ManyToManyField(blank=True, to='chatnoir_api.apikeyrole', verbose_name='API Key Roles'),
        ),
        migrations.AddField(
            model_name='apikey',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='api_key', to='chatnoir_api.apiuser', verbose_name='API User'),
        ),
        migrations.CreateModel(
            name='ApiConfiguration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('default_issue_key', models.ForeignKey(help_text='Default parent key for new keys', on_delete=django.db.models.deletion.CASCADE, to='chatnoir_api.apikey', verbose_name='Default API Issue Key')),
            ],
            options={
                'verbose_name': 'Global Configuration',
            },
        ),
        migrations.CreateModel(
            name='PasscodeRedemption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('redemption_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('api_key', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='chatnoir_api.apikey')),
                ('passcode', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='chatnoir_api.apikeypasscode')),
            ],
            options={
                'verbose_name': 'Passcode Redemption Log',
                'verbose_name_plural': 'Passcode Redemption Log',
                'unique_together': {('api_key', 'passcode')},
            },
        ),
        migrations.CreateModel(
            name='ApiPendingUser',
            fields=[
                ('activation_code', models.CharField(default=chatnoir_api.models.generate_apikey, max_length=255, primary_key=True, serialize=False, verbose_name='Activation Code')),
                ('common_name', models.CharField(max_length=100, verbose_name='Common Name')),
                ('email', models.EmailField(max_length=200, verbose_name='Email Address')),
                ('organization', models.CharField(blank=True, max_length=100, null=True, verbose_name='Organization')),
                ('address', models.CharField(blank=True, max_length=200, null=True, verbose_name='Address')),
                ('zip_code', models.CharField(blank=True, max_length=50, null=True, verbose_name='ZIP Code')),
                ('state', models.CharField(blank=True, max_length=50, null=True, verbose_name='State')),
                ('country', django_countries.fields.CountryField(blank=True, max_length=50, null=True, verbose_name='Country')),
                ('comments', models.TextField(blank=True, max_length=200, null=True, verbose_name='Comments')),
                ('email_verified', models.BooleanField(default=False, verbose_name='Email verified')),
                ('issue_key', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='chatnoir_api.apikey', verbose_name='Issue Key')),
                ('passcode', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='chatnoir_api.apikeypasscode', verbose_name='Passcode')),
            ],
            options={
                'verbose_name': 'Pending User',
                'verbose_name_plural': 'Pending Users',
                'unique_together': {('email', 'passcode')},
            },
        ),
    ]
