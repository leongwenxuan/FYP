# Generated by Django 4.2.17 on 2025-03-22 07:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fypapp', '0002_agency_issueassignment_staffprofile_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='agency',
            name='name',
            field=models.CharField(choices=[('Government', 'Government')], max_length=100),
        ),
        migrations.AlterField(
            model_name='staffprofile',
            name='role',
            field=models.CharField(choices=[('admin', 'Agency Admin')], max_length=20),
        ),
    ]
