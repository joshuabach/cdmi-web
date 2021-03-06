# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-14 09:45
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Provider',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('client_name', models.CharField(max_length=200)),
                ('client_id', models.CharField(max_length=200)),
                ('client_secret', models.CharField(max_length=200)),
                ('redirect_uri', models.URLField()),
                ('provider_uri', models.URLField()),
                ('openid_configuration', models.TextField()),
            ],
        ),
    ]
