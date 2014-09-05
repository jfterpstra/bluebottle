from django.core.urlresolvers import reverse
from bluebottle.payments.models import Payment
from bluebottle.payments_docdata.models import DocdataPayment
from polymorphic.admin import PolymorphicChildModelAdmin


class MchangaPaymentAdmin(PolymorphicChildModelAdmin):
    base_model = Payment
    model = DocdataPayment

    readonly_fields = ('mpesa_confirmation', 'order_payment_link')

    fields = ('status', ) + readonly_fields

    def order_payment_link(self, obj):
        object = obj.order_payment
        print object._meta.app_label
        print object._meta.module_name
        url = reverse('admin:{0}_{1}_change'.format(object._meta.app_label, object._meta.module_name), args=[object.id])
        print url
        return "<a href='{0}'>Order Payment: {1}</a>".format(str(url), object.id)

    order_payment_link.allow_tags = True