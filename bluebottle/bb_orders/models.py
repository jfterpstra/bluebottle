from bluebottle.utils.model_dispatcher import get_donation_model
from django.conf import settings
from django.db import models
from django.db.models.aggregates import Sum
from django.utils.translation import ugettext as _
from django_extensions.db.fields import ModificationDateTimeField, CreationDateTimeField
from djchoices import DjangoChoices, ChoiceItem
from uuidfield import UUIDField
from django.db.models import options
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver

options.DEFAULT_NAMES = options.DEFAULT_NAMES + ('default_serializer','preview_serializer', 'manage_serializer')

DONATION_MODEL = get_donation_model()


class BaseOrder(models.Model):
    """
    An order is a collection of OrderItems and vouchers with a connected payment.
    """
    class OrderStatuses(DjangoChoices):
        new = ChoiceItem('new', label=_("new"))
        locked = ChoiceItem('locked', label=_("Locked"))
        closed = ChoiceItem('closed', label=_("Closed"))

    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("user"), blank=True, null=True)
    status = models.CharField(_("Status"), max_length=20, choices=OrderStatuses.choices, default=OrderStatuses.new, db_index=True)

    created = CreationDateTimeField(_("Created"))
    updated = ModificationDateTimeField(_("Updated"))
    closed = models.DateTimeField(_("Closed"), blank=True, editable=False, null=True)

    total = models.DecimalField(_("Amount"), max_digits=16, decimal_places=2, default=0)

    def update_total(self, save=True):
        donations = DONATION_MODEL.objects.filter(order=self)
        self.total = donations.aggregate(Sum('amount'))['amount__sum']
        if save:
            self.save()

    def set_status(self, status, save=True):
        self.status = status
        if save:
            self.save()

    def __unicode__(self):
        return "{0} : {1}".format(self.id, self.created)

    class Meta:
        abstract = True
        default_serializer = 'bluebottle.bb_orders.serializers.OrderSerializer'
        preview_serializer = 'bluebottle.bb_orders.serializers.OrderSerializer'
        manage_serializer = 'bluebottle.bb_orders.serializers.ManageOrderSerializer'


@receiver(post_save, weak=False, sender=DONATION_MODEL, dispatch_uid='donation_model')
def update_order_amount(sender, instance, **kwargs):
    instance.order.update_total()


@receiver(post_delete, weak=False, sender=DONATION_MODEL, dispatch_uid='donation_model')
def update_order_amount(sender, instance, **kwargs):
    instance.order.update_total()
