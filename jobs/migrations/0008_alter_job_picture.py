# Generated by Django 4.2.16 on 2025-03-12 22:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0007_alter_job_picture'),
    ]

    operations = [
        migrations.AlterField(
            model_name='job',
            name='picture',
            field=models.ImageField(blank=True, null=True, upload_to='job_pictures/'),
        ),
    ]
