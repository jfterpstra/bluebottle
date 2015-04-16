# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):


    def forwards(self, orm):
        db.rename_table('bb_payouts_projectpayoutlog', 'payouts_projectpayoutlog')
        db.rename_table('bb_payouts_organizationpayoutlog', 'payouts_organizationpayoutlog')

        orm['contenttypes.contenttype'].objects.filter(
            app_label='bb_payouts',
            model='projectpayoutlog',
        ).update(app_label='payouts')

        orm['contenttypes.contenttype'].objects.filter(
            app_label='bb_payouts',
            model='organizationpayoutlog',
        ).update(app_label='payouts')


    def backwards(self, orm):
        db.rename_table('payouts_projectpayoutlog', 'bb_payouts_projectpayoutlog')
        db.rename_table('payouts_organizationpayoutlog', 'bb_payouts_organizationpayoutlog')

        orm['contenttypes.contenttype'].objects.filter(
            app_label='payouts',
            model='projectpayoutlog',
        ).update(app_label='bb_payouts')

        orm['contenttypes.contenttype'].objects.filter(
            app_label='_payouts',
            model='organizationpayoutlog',
        ).update(app_label='bb_payouts')

    models = {
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['contenttypes', 'bb_payouts']