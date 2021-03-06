from bluebottle.terms.models import Terms, TermsAgreement
from rest_framework import serializers
from bluebottle.members.models import Member
from bluebottle.terms.models import Terms
\

class TermsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Terms
        fields = ('id', 'date', 'version', 'contents')


class TermsAgreementSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    terms = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = TermsAgreement
        fields = ('id', 'terms', 'user', 'created')
