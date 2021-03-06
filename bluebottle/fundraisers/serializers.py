from django.utils.translation import ugettext as _
from rest_framework import serializers

from bluebottle.bluebottle_drf2.serializers import ImageSerializer, OEmbedField
from bluebottle.fundraisers.models import Fundraiser
from bluebottle.members.serializers import UserProfileSerializer
from bluebottle.projects.models import Project


class ImageSerializerExt(ImageSerializer):
    """
    Adds semi-logic behaviour for PUT requests (update) to ignore the required flag if the passed URL is identical to
    the existing URL. The PUT-request should actually pass the file object again but this is impractical.
    """

    def field_from_native(self, data, files, field_name, into):
        request = self.context.get('request')

        if request.method == 'PUT' and self.required and field_name in data:
            from django.conf import settings
            from sorl.thumbnail.shortcuts import get_thumbnail

            existing_value = getattr(self.parent.object, field_name)

            provided_full_url = data[field_name]['full']
            expected_full_url = settings.MEDIA_URL + unicode(
                get_thumbnail(existing_value, '800x600'))

            if provided_full_url.endswith(expected_full_url):
                return

        if request.method == 'PUT' and field_name not in data and not files:
            return

        return super(ImageSerializerExt, self).field_from_native(data, files,
                                                                 field_name,
                                                                 into)


class BaseFundraiserSerializer(serializers.ModelSerializer):
    """ Serializer to view/create fundraisers """

    owner = UserProfileSerializer(read_only=True)
    project = serializers.SlugRelatedField(slug_field='slug',
                                           queryset=Project.objects)
    image = ImageSerializerExt()
    amount_donated = serializers.DecimalField(max_digits=16,
                                              decimal_places=2,
                                              read_only=True)
    video_html = OEmbedField(source='video_url', maxwidth='560',
                             maxheight='315')

    class Meta:
        model = Fundraiser
        fields = ('id', 'owner', 'project', 'title', 'description', 'image',
                  'created', 'video_html', 'video_url', 'amount',
                  'amount_donated', 'deadline')

    def validate(self, data):
        if not data['deadline'] or data['deadline'] > data['project'].deadline:
            raise serializers.ValidationError(
                {'deadline': [_("Fundraiser deadline exceeds project deadline.")]}
            )
        return data
