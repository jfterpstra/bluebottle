from rest_framework import serializers

from bluebottle.donations.serializers import ManageDonationSerializer
from bluebottle.orders.models import Order
from bluebottle.members.models import Member


class OrderSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=Order.STATUS_CHOICES, read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Order
        fields = ('id', 'user', 'created')


class ManageOrderSerializer(serializers.ModelSerializer):
    total = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)
    status = serializers.ChoiceField(choices=Order.STATUS_CHOICES, read_only=True)
    user = serializers.PrimaryKeyRelatedField(queryset=Member.objects, required=False, allow_null=True)
    donations = ManageDonationSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ('id', 'user', 'total', 'status', 'donations', 'created')
