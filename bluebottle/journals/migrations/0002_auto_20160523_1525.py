# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-05-23 13:25
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('donations', '0003_donation_order'),
        ('journals', '0001_initial'),
        ('payments', '0001_initial'),
        ('payouts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectpayoutjournal',
            name='payout',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='journal_set', to='payouts.ProjectPayout'),
        ),
        migrations.AddField(
            model_name='organizationpayoutjournal',
            name='payout',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='journal_set', to='payouts.OrganizationPayout'),
        ),
        migrations.AddField(
            model_name='orderpaymentjournal',
            name='order_payment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='journals', to='payments.OrderPayment'),
        ),
        migrations.AddField(
            model_name='donationjournal',
            name='donation',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='journal_set', to='donations.Donation'),
        ),
    ]