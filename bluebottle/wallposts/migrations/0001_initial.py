# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-05-23 13:25
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('donations', '0004_auto_20160523_1525'),
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='MediaWallpostPhoto',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('photo', models.ImageField(upload_to=b'mediawallpostphotos')),
                ('deleted', models.DateTimeField(blank=True, null=True, verbose_name='deleted')),
                ('ip_address', models.GenericIPAddressField(blank=True, default=None, null=True, verbose_name='IP address')),
                ('author', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='mediawallpostphoto_wallpost_photo', to=settings.AUTH_USER_MODEL, verbose_name='author')),
                ('editor', models.ForeignKey(blank=True, help_text='The last user to edit this wallpost photo.', null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='editor')),
            ],
        ),
        migrations.CreateModel(
            name='Reaction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField(max_length=300, verbose_name='reaction text')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('updated', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='updated')),
                ('deleted', models.DateTimeField(blank=True, null=True, verbose_name='deleted')),
                ('ip_address', models.GenericIPAddressField(blank=True, default=None, null=True, verbose_name='IP address')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='wallpost_reactions', to=settings.AUTH_USER_MODEL, verbose_name='author')),
                ('editor', models.ForeignKey(blank=True, help_text='The last user to edit this reaction.', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='editor')),
            ],
            options={
                'ordering': ('created',),
                'verbose_name': 'Reaction',
                'verbose_name_plural': 'Reactions',
            },
        ),
        migrations.CreateModel(
            name='Wallpost',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('updated', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='updated')),
                ('deleted', models.DateTimeField(blank=True, null=True, verbose_name='deleted')),
                ('ip_address', models.GenericIPAddressField(blank=True, default=None, null=True, verbose_name='IP address')),
                ('object_id', models.PositiveIntegerField(verbose_name='object ID')),
                ('share_with_facebook', models.BooleanField(default=False)),
                ('share_with_twitter', models.BooleanField(default=False)),
                ('share_with_linkedin', models.BooleanField(default=False)),
                ('email_followers', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ('created',),
            },
        ),
        migrations.CreateModel(
            name='MediaWallpost',
            fields=[
                ('wallpost_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='wallposts.Wallpost')),
                ('title', models.CharField(max_length=60)),
                ('text', models.TextField(blank=True, default=b'', max_length=300)),
                ('video_url', models.URLField(blank=True, default=b'', max_length=100)),
            ],
            options={
                'abstract': False,
            },
            bases=('wallposts.wallpost',),
        ),
        migrations.CreateModel(
            name='SystemWallpost',
            fields=[
                ('wallpost_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='wallposts.Wallpost')),
                ('text', models.TextField(blank=True, max_length=300)),
                ('related_id', models.PositiveIntegerField(verbose_name='related ID')),
                ('related_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType', verbose_name='related type')),
            ],
            options={
                'abstract': False,
            },
            bases=('wallposts.wallpost',),
        ),
        migrations.CreateModel(
            name='TextWallpost',
            fields=[
                ('wallpost_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='wallposts.Wallpost')),
                ('text', models.TextField(max_length=300)),
            ],
            options={
                'abstract': False,
            },
            bases=('wallposts.wallpost',),
        ),
        migrations.AddField(
            model_name='wallpost',
            name='author',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='wallpost_wallpost', to=settings.AUTH_USER_MODEL, verbose_name='author'),
        ),
        migrations.AddField(
            model_name='wallpost',
            name='content_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='content_type_set_for_wallpost', to='contenttypes.ContentType', verbose_name='content type'),
        ),
        migrations.AddField(
            model_name='wallpost',
            name='donation',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='donation', to='donations.Donation', verbose_name='Donation'),
        ),
        migrations.AddField(
            model_name='wallpost',
            name='editor',
            field=models.ForeignKey(blank=True, help_text='The last user to edit this wallpost.', null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='editor'),
        ),
        migrations.AddField(
            model_name='wallpost',
            name='polymorphic_ctype',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='polymorphic_wallposts.wallpost_set+', to='contenttypes.ContentType'),
        ),
        migrations.AddField(
            model_name='reaction',
            name='wallpost',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reactions', to='wallposts.Wallpost'),
        ),
        migrations.AddField(
            model_name='mediawallpostphoto',
            name='mediawallpost',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='photos', to='wallposts.MediaWallpost'),
        ),
    ]
