# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-05-23 13:25
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BankAccount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('account_nr', models.CharField(blank=True, max_length=35, verbose_name='account number')),
                ('account_name', models.CharField(max_length=50, verbose_name='account name')),
            ],
        ),
        migrations.CreateModel(
            name='BankTransaction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sender_account', models.CharField(max_length=35, verbose_name='holder account number')),
                ('currency', models.CharField(max_length=3, verbose_name='currency')),
                ('interest_date', models.DateField(verbose_name='interest date')),
                ('credit_debit', models.CharField(choices=[(b'C', 'Credit'), (b'D', 'Debit')], db_index=True, max_length=1, verbose_name='credit/debit')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=14, verbose_name='amount')),
                ('counter_account', models.CharField(max_length=35, verbose_name='recipient account')),
                ('counter_name', models.CharField(max_length=70, verbose_name='recipient name')),
                ('book_date', models.DateField(db_index=True, verbose_name='book date')),
                ('book_code', models.CharField(max_length=2, verbose_name='book code')),
                ('filler', models.CharField(blank=True, max_length=6, verbose_name='filler')),
                ('description1', models.CharField(blank=True, max_length=35, verbose_name='description 1')),
                ('description2', models.CharField(blank=True, max_length=35, verbose_name='description 2')),
                ('description3', models.CharField(blank=True, max_length=35, verbose_name='description 3')),
                ('description4', models.CharField(blank=True, max_length=35, verbose_name='description 4')),
                ('description5', models.CharField(blank=True, max_length=35, verbose_name='description 5')),
                ('description6', models.CharField(blank=True, max_length=35, verbose_name='description 6')),
                ('end_to_end_id', models.CharField(blank=True, max_length=35, verbose_name='End to end ID')),
                ('id_recipient', models.CharField(blank=True, max_length=35, verbose_name='ID recipient account')),
                ('mandate_id', models.CharField(blank=True, max_length=35, verbose_name='Mandate ID')),
                ('status', models.CharField(blank=True, choices=[(b'valid', 'Valid'), (b'unknown', 'Invalid: Unknown transaction'), (b'mismatch', 'Invalid: Amount mismatch')], help_text='Cached status assigned during matching.', max_length=30, verbose_name='status')),
                ('status_remarks', models.CharField(blank=True, help_text='Additional remarks regarding the status.', max_length=250, verbose_name='status remarks')),
            ],
            options={
                'verbose_name': 'bank transaction',
                'verbose_name_plural': 'bank transactions',
            },
        ),
        migrations.CreateModel(
            name='BankTransactionCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Name')),
            ],
            options={
                'verbose_name': 'Bank transaction category',
                'verbose_name_plural': 'Bank transaction categories',
            },
        ),
        migrations.CreateModel(
            name='BankTransactionTenant',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=35, verbose_name='Tenant name')),
            ],
        ),
        migrations.CreateModel(
            name='RemoteDocdataPayment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('merchant_reference', models.CharField(db_index=True, max_length=35, verbose_name='merchant reference')),
                ('triple_deal_reference', models.CharField(db_index=True, max_length=40, verbose_name='Triple Deal reference')),
                ('payment_type', models.CharField(db_index=True, max_length=15, verbose_name='type')),
                ('amount_collected', models.DecimalField(decimal_places=2, max_digits=14, verbose_name='amount collected')),
                ('currency_amount_collected', models.CharField(max_length=3, verbose_name='currency of amount collected')),
                ('tpcd', models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True, verbose_name='TPCD')),
                ('currency_tpcd', models.CharField(blank=True, max_length=3, verbose_name='currency of TPCD')),
                ('tpci', models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True, verbose_name='TPCI')),
                ('currency_tpci', models.CharField(blank=True, max_length=3, verbose_name='currency of TPCI')),
                ('docdata_fee', models.DecimalField(decimal_places=2, max_digits=14, verbose_name='Docdata payments fee')),
                ('currency_docdata_fee', models.CharField(max_length=3, verbose_name='currency of Docdata payments fee')),
                ('status', models.CharField(blank=True, choices=[(b'valid', 'Valid'), (b'inconsistent_chargeback', 'Invalid: inconsistent chargeback'), (b'missing', 'Invalid: Missing backoffice record'), (b'mismatch', 'Invalid: Amount mismatch')], help_text='Cached status assigned during matching.', max_length=30, verbose_name='status')),
                ('status_remarks', models.CharField(blank=True, help_text='Additional remarks regarding the status.', max_length=250, verbose_name='status remarks')),
            ],
            options={
                'ordering': ('-remote_payout__payout_date',),
            },
        ),
        migrations.CreateModel(
            name='RemoteDocdataPayout',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payout_reference', models.CharField(max_length=100, unique=True, verbose_name='Payout Reference')),
                ('payout_date', models.DateField(blank=True, db_index=True, null=True, verbose_name='Payout date')),
                ('start_date', models.DateField(blank=True, db_index=True, null=True, verbose_name='Start date')),
                ('end_date', models.DateField(blank=True, db_index=True, null=True, verbose_name='End date')),
                ('collected_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True, verbose_name='Collected amount')),
                ('payout_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True, verbose_name='Payout amount')),
            ],
            options={
                'ordering': ('-payout_date',),
            },
        ),
    ]
