# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-09 11:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cdmi', '0002_site_auth'),
    ]

    operations = [
        migrations.AddField(
            model_name='site',
            name='browser_module',
            field=models.CharField(blank=True, default='', max_length=128),
        ),
    ]
