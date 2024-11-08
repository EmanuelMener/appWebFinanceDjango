# Generated by Django 5.1.2 on 2024-11-03 20:12

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gestao_financeiro', '0007_transacao_importado_ofx'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name='grupo',
            name='descricao',
        ),
        migrations.AddField(
            model_name='grupo',
            name='criador',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='grupos_criados', to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
    ]
