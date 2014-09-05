from decimal import Decimal as D

from django.utils.translation import ugettext as _
from django.db import models

from bluebottle.payments.models import Payment


class MchangaPayment(Payment):

    mpesa_confirmation = models.CharField(_("Mpesa Confirmation"), max_length=100, default='')
    mpesa_name = models.CharField(_("Mpesa Name"), max_length=100, default='')
    phone_number = models.CharField(_("Phone number"), max_length=100, default='')
    amount = models.IntegerField()