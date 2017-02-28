# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-14 10:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('openid', '0002_auto_20170214_0958'),
    ]

    operations = [
        migrations.AddField(
            model_name='provider',
            name='authorization_endpoint',
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name='provider',
            name='introspection_endpoint',
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name='provider',
            name='token_endpoint',
            field=models.URLField(blank=True),
        ),
    ]