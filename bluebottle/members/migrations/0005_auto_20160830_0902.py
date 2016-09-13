# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-08-30 07:02
from __future__ import unicode_literals

from django.db import migrations


def add_export_permission(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    try:
        content_type = ContentType.objects.get(app_label='sites', model='site')
        perm, created = Permission.objects.get_or_create(codename='export',
                                                         name='Can export platform data',
                                                         content_type=content_type)
        staff = Group.objects.get(name='Staff')
        staff.permissions.add(perm)
    except ContentType.DoesNotExist:
        pass


def remove_export_permission(apps, schema_editor):
    Permission = apps.get_model("auth", "Permission")
    Permission.objects.filter(codename='export',
                              name='Can export platform data').delete()

class Migration(migrations.Migration):

    dependencies = [
        ('members', '0004_member_verified'),
    ]

    operations = [
        migrations.RunPython(add_export_permission, remove_export_permission)
    ]