# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-12-14 14:31
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0010_auto_20161214_1429'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='SupportersContent',
            new_name='SupporterTotalContent',
        ),
        migrations.AlterModelTable(
            name='supportertotalcontent',
            table='contentitem_cms_supportertotalcontent',
        ),
    ]
