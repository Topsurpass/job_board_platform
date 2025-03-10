# Generated by Django 4.2.16 on 2025-03-02 01:57

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('applications', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='application',
            name='cover_letter',
            field=models.TextField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='application',
            name='resume_link',
            field=models.URLField(default=django.utils.timezone.now, max_length=255),
            preserve_default=False,
        ),
    ]
