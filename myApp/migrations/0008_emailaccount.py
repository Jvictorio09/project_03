# Generated manually for EmailAccount model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('myApp', '0007_hiddenproperty'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailAccount',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('email_address', models.EmailField(help_text='Email address for sending')),
                ('display_name', models.CharField(help_text="Display name for emails (e.g., 'John Doe' or 'Company Name')", max_length=255)),
                ('access_token', models.TextField(help_text='Gmail API access token')),
                ('refresh_token', models.TextField(help_text='Gmail API refresh token')),
                ('token_expires_at', models.DateTimeField(help_text='When the access token expires')),
                ('provider', models.CharField(choices=[('gmail', 'Gmail'), ('postmark', 'Postmark'), ('sendgrid', 'SendGrid')], default='gmail', max_length=20)),
                ('google_id', models.CharField(blank=True, help_text='Google user ID', max_length=100)),
                ('is_active', models.BooleanField(default=True, help_text='Whether this account can send emails')),
                ('is_primary', models.BooleanField(default=False, help_text='Primary email account for organization')),
                ('is_verified', models.BooleanField(default=False, help_text='Whether the email connection is verified')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('last_used_at', models.DateTimeField(blank=True, help_text='Last time this account was used to send emails', null=True)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='email_accounts', to='myApp.organization')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='email_accounts', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-is_primary', '-created_at'],
                'indexes': [
                    models.Index(fields=['organization', 'is_active'], name='myapp_emaila_organiz_2b8a0b_idx'),
                    models.Index(fields=['organization', 'is_primary'], name='myapp_emaila_organiz_4a8b1c_idx'),
                ],
            },
        ),
        migrations.AddConstraint(
            model_name='emailaccount',
            constraint=models.UniqueConstraint(fields=('organization', 'email_address'), name='unique_org_email'),
        ),
    ]
