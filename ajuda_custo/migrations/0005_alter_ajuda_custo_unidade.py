# Generated by Django 5.0.7 on 2024-08-26 18:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ajuda_custo', '0004_alter_ajuda_custo_matricula'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ajuda_custo',
            name='unidade',
            field=models.CharField(max_length=100),
        ),
    ]