from rest_framework import serializers
from django_iban.validators import iban_validator, swift_bic_validator

from bluebottle.bluebottle_drf2.serializers import PrivateFileSerializer
from bluebottle.utils.serializers import AddressSerializer, URLField
from bluebottle.utils.model_dispatcher import (
    get_organization_model, get_organizationmember_model, get_organizationdocument_model)

from .models import Organization, OrganizationDocument


ORGANIZATION_MODEL = get_organization_model()
MEMBER_MODEL = get_organizationmember_model()
DOCUMENT_MODEL = get_organizationdocument_model()

ORGANIZATION_FIELDS = ( 'id', 'name', 'slug', 'address_line1', 'address_line2',
                        'city', 'state', 'country', 'postal_code', 'phone_number',
                        'website', 'email', 'twitter', 'facebook', 'skype', 'documents',
                        'person')


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ORGANIZATION_MODEL
        fields = ORGANIZATION_FIELDS


class OrganizationDocumentSerializer(serializers.ModelSerializer):
    file = PrivateFileSerializer()

    class Meta:
        model = DOCUMENT_MODEL
        fields = ('id', 'organization', 'file')


class ManageOrganizationSerializer(OrganizationSerializer):

    slug = serializers.SlugField(required=False)

    documents = OrganizationDocumentSerializer(
        many=True, source='documents', read_only=True)

    name = serializers.CharField(required=True)
    website = URLField(required=False)
    email = serializers.EmailField(required=False)
    twitter = serializers.CharField(required=False)
    facebook = serializers.CharField(required=False)
    skype = serializers.CharField(required=False)

    class Meta:
        model = ORGANIZATION_MODEL
        fields = ORGANIZATION_FIELDS + ('partner_organizations',
                                        'created', 'updated')

