# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-04-25 08:06
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cdmi', '0007_auto_20170425_0750'),
    ]

    operations = [
        migrations.AlterField(
            model_name='webdavserver',
            name='login',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AlterField(
            model_name='webdavserver',
            name='passwd',
            field=models.CharField(blank=True, max_length=200),
        ),
    ]
