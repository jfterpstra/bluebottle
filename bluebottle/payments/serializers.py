from bluebottle.bluebottle_drf2.serializers import ObjectFieldSerializer
from bluebottle.payments.models import OrderPayment, PaymentAction
from rest_framework import serializers


class PaymentActionSerializer(serializers.ModelSerializer):

    class Meta:
        model = PaymentAction
        fields = ('type', 'method', 'url', 'payload')


class ManagePaymentSerializer(serializers.ModelSerializer):

    status = serializers.CharField(read_only=True)
    amount = serializers.DecimalField(read_only=True)
    authorization_action = PaymentActionSerializer()
    integration_data = ObjectFieldSerializer()

    class Meta:
        model = OrderPayment
        fields = ('id', 'order', 'payment_method', 'integration_data', 'amount', 'status', 'authorization_action')