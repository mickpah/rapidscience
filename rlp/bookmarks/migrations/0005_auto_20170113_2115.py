# -*- coding: utf-8 -*-
# Generated by Django 1.9.10 on 2017-01-13 21:15
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookmarks', '0004_auto_20161101_1757'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bookmark',
            name='name',
            field=models.CharField(blank=True, max_length=500),
        ),
    ]
