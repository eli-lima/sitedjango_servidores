# Generated by Django 5.0.7 on 2024-08-09 22:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('seappb', '0004_alter_usuario_matricula'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usuario',
            name='foto_perfil',
            field=models.ImageField(default='profile_pics/default.jpg', upload_to='profile_pics'),
        ),
    ]