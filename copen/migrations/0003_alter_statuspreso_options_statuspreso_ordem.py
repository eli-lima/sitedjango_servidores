# Generated by Django 5.0.7 on 2025-02-13 20:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('copen', '0002_statuspreso_atendimento_status_preso'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='statuspreso',
            options={'ordering': ['ordem']},
        ),
        migrations.AddField(
            model_name='statuspreso',
            name='ordem',
            field=models.IntegerField(default=0),
        ),
    ]
