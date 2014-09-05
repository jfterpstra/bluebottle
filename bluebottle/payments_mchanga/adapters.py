# coding=utf-8
import logging
from bluebottle.payments.adapters import BasePaymentAdapter
from bluebottle.utils.utils import StatusDefinition
from .models import MchangaPayment

logger = logging.getLogger(__name__)


class MchangaPaymentAdapter(BasePaymentAdapter):

    MODEL_CLASS = MchangaPayment

    STATUS_MAPPING = {
        'NEW':                            StatusDefinition.STARTED,
        'STARTED':                        StatusDefinition.STARTED,
        'REDIRECTED_FOR_AUTHENTICATION':  StatusDefinition.STARTED, # Is this mapping correct?
        'AUTHORIZATION_REQUESTED':        StatusDefinition.STARTED, # Is this mapping correct?
        'AUTHORIZED':                     StatusDefinition.AUTHORIZED,
        'PAID':                           StatusDefinition.SETTLED, 
        'CANCELLED':                      StatusDefinition.CANCELLED,
        'CHARGED_BACK':                   StatusDefinition.CHARGED_BACK,
        'CONFIRMED_PAID':                 StatusDefinition.PAID,
        'CONFIRMED_CHARGEDBACK':          StatusDefinition.CHARGED_BACK,
        'CLOSED_SUCCESS':                 StatusDefinition.PAID,
        'CLOSED_CANCELLED':               StatusDefinition.CANCELLED,
    }

    def get_status_mapping(self, external_payment_status):
        return self.STATUS_MAPPING.get(external_payment_status)

    def create_payment(self):
        payment = self.MODEL_CLASS(order_payment=self.order_payment, **self.order_payment.integration_data)
        payment.amount = self.order_payment.amount
        payment.save()
        return payment

    def get_authorization_action(self):
        return {'type': 'success'}

    def check_payment_status(self):
        pass