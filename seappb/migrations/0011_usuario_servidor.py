# Generated by Django 5.0.7 on 2025-04-28 00:21

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('seappb', '0010_alter_permissaosecao_unique_together_and_more'),
        ('servidor', '0007_servidor_disposicao'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='servidor',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='servidor.servidor'),
        ),
    ]
