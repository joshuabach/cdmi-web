# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-14 13:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('openid', '0003_auto_20170214_1020'),
    ]

    operations = [
        migrations.AddField(
            model_name='provider',
            name='jwks_uri',
            field=models.URLField(blank=True),
        ),
    ]
