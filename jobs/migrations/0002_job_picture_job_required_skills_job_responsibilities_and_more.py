# Generated by Django 4.2.16 on 2025-03-04 03:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='picture',
            field=models.ImageField(blank=True, null=True, upload_to='job_pictures/'),
        ),
        migrations.AddField(
            model_name='job',
            name='required_skills',
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name='job',
            name='responsibilities',
            field=models.JSONField(default=list),
        ),
        migrations.AlterField(
            model_name='job',
            name='type',
            field=models.JSONField(default=list),
        ),
    ]
