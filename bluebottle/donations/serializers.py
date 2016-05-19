# coding=utf-8
from bluebottle.utils.serializer_dispatcher import get_serializer_class
from rest_framework import serializers

from bluebottle.utils.model_dispatcher import get_donation_model
from bluebottle.projects.serializers import \
    ProjectPreviewSerializer as BaseProjectPreviewSerializer

DONATION_MODEL = get_donation_model()


class ManageDonationSerializer(serializers.ModelSerializer):
    project = serializers.SlugRelatedField(slug_field='slug')
    fundraiser = serializers.PrimaryKeyRelatedField(required=False)
    order = serializers.PrimaryKeyRelatedField()
    amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, max_value=1500000
    )
    status = serializers.CharField(source='status', read_only=True)

    class Meta:
        model = DONATION_MODEL
        fields = ('id', 'project', 'fundraiser', 'amount', 'status', 'order',
                  'anonymous', 'completed', 'created', 'reward')

        # FIXME Add validations for amount and project phase


class PreviewDonationSerializer(serializers.ModelSerializer):
    project = get_serializer_class('PROJECTS_PROJECT_MODEL', 'preview')
    fundraiser = serializers.PrimaryKeyRelatedField(required=False)
    payment_method = serializers.SerializerMethodField('get_payment_method')
    user = get_serializer_class('AUTH_USER_MODEL', 'preview')(
        source='public_user')

    class Meta:
        model = DONATION_MODEL
        fields = ('id', 'project', 'fundraiser', 'user', 'created',
                  'payment_method', 'anonymous', 'amount', 'reward')

    def get_payment_method(self, obj):
        return obj.get_payment_method



class PreviewDonationWithoutAmountSerializer(PreviewDonationSerializer):
    payment_method = serializers.SerializerMethodField('get_payment_method')

    class Meta:
        model = DONATION_MODEL
        fields = ('id', 'project', 'fundraiser', 'user', 'created',
                  'anonymous')

    def get_payment_method(self, obj):
        return obj.get_payment_method

class DefaultDonationSerializer(PreviewDonationSerializer):
    class Meta:
        model = DONATION_MODEL
        fields = PreviewDonationSerializer.Meta.fields + ('amount', 'reward')


class LatestDonationProjectSerializer(BaseProjectPreviewSerializer):
    task_count = serializers.IntegerField(source='task_count')
    owner = get_serializer_class('AUTH_USER_MODEL', 'preview')(source='owner')

    class Meta(BaseProjectPreviewSerializer):
        model = BaseProjectPreviewSerializer.Meta.model
        fields = ('id', 'title', 'image', 'status', 'pitch', 'country',
                  'task_count', 'allow_overfunding', 'is_campaign',
                  'amount_asked', 'amount_donated', 'amount_needed',
                  'deadline', 'status', 'owner')


class LatestDonationSerializer(serializers.ModelSerializer):
    project = LatestDonationProjectSerializer()
    user = get_serializer_class('AUTH_USER_MODEL', 'preview')()
    payment_method = serializers.SerializerMethodField('get_payment_method')

    class Meta:
        model = DONATION_MODEL
        fields = ('id', 'project', 'fundraiser', 'user', 'created',
                  'anonymous', 'amount')

    def get_payment_method(self, obj):
        return obj.get_payment_method
