from bluebottle.bb_accounts.models import UserAddress
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.hashers import UNUSABLE_PASSWORD_PREFIX

from rest_framework import serializers

from bluebottle.bluebottle_drf2.serializers import (
    SorlImageField, ImageSerializer)

from bluebottle.clients import properties
from bluebottle.tasks.models import Skill
from bluebottle.geo.models import Location
from bluebottle.bb_projects.models import ProjectTheme
from bluebottle.geo.serializers import LocationSerializer, CountrySerializer
from bluebottle.geo.models import Location
from bluebottle.tasks.models import Skill
from bluebottle.bb_projects.models import ProjectTheme

BB_USER_MODEL = get_user_model()


class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAddress
        fields = ('id', 'line1', 'line2', 'address_type',
                  'city', 'state', 'country', 'postal_code')


class UserPreviewSerializer(serializers.ModelSerializer):
    """
    Serializer for a subset of a member's public profile. This is usually
    embedded into other serializers.
    """

    def __init__(self, *args, **kwargs):
        kwargs['read_only'] = True
        super(UserPreviewSerializer, self).__init__(*args, **kwargs)

    avatar = SorlImageField('133x133', source='picture', crop='center')

    # TODO: Remove first/last name and only use these
    full_name = serializers.ReadOnlyField(source='get_full_name', read_only=True)
    short_name = serializers.ReadOnlyField(source='get_short_name', read_only=True)

    class Meta:
        model = BB_USER_MODEL
        fields = ('id', 'first_name', 'last_name', 'username',
                  'avatar', 'full_name', 'short_name')


class CurrentUserSerializer(UserPreviewSerializer):
    """
    Serializer for the current authenticated user. This is the same as the
    serializer for the member preview with the
    addition of id_for_ember.
    """
    # This is a hack to work around an issue with Ember-Data keeping the id as
    # 'current'.
    id_for_ember = serializers.IntegerField(source='id', read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    country = CountrySerializer(source='address.country')
    location = LocationSerializer()

    class Meta:
        model = BB_USER_MODEL
        fields = UserPreviewSerializer.Meta.fields + (
            'id_for_ember', 'primary_language', 'email', 'full_name',
            'last_login', 'date_joined', 'task_count', 'project_count',
            'has_projects', 'donation_count', 'fundraiser_count', 'location',
            'country')




class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for a member's public profile.
    """
    url = serializers.HyperlinkedIdentityField(view_name='user-profile-detail',
                                               lookup_field='pk')
    picture = ImageSerializer(required=False)
    date_joined = serializers.DateTimeField(read_only=True)

    # TODO: Remove first/last name and only use these
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    short_name = serializers.CharField(source='get_short_name', read_only=True)

    primary_language = serializers.CharField(required=False,
                                             default=properties.LANGUAGE_CODE)
    location = serializers.PrimaryKeyRelatedField(required=False, allow_null=True,
                                                  queryset=Location.objects)
    avatar = SorlImageField('133x133', source='picture', crop='center',
                            required=False)

    skill_ids = serializers.PrimaryKeyRelatedField(many=True,
                                                   source='skills',
                                                   required=False,
                                                   queryset=Skill.objects)
    favourite_theme_ids = serializers.PrimaryKeyRelatedField(
        many=True, source='favourite_themes', queryset=ProjectTheme.objects)

    project_count = serializers.ReadOnlyField()
    donation_count = serializers.ReadOnlyField()
    fundraiser_count = serializers.ReadOnlyField()
    task_count = serializers.ReadOnlyField()
    time_spent = serializers.ReadOnlyField()
    tasks_performed = serializers.ReadOnlyField()

    class Meta:
        model = BB_USER_MODEL
        fields = ('id', 'url', 'full_name', 'short_name', 'picture',
                  'primary_language', 'about_me', 'location', 'avatar',
                  'project_count', 'donation_count', 'date_joined',
                  'fundraiser_count', 'task_count', 'time_spent',
                  'tasks_performed', 'website', 'twitter', 'facebook',
                  'skypename', 'skill_ids', 'favourite_theme_ids')


class ManageProfileSerializer(UserProfileSerializer):
    """
    Serializer for the a member's private profile.
    """
    partial = True
    address = UserAddressSerializer(allow_null=True)

    class Meta:
        model = BB_USER_MODEL
        fields = UserProfileSerializer.Meta.fields + (
            'email', 'address', 'newsletter', 'campaign_notifications', 'location',
            'birthdate', 'gender', 'first_name', 'last_name', 'username'
        )

    def update(self, instance, validated_data):
        address = validated_data.pop('address', {})
        for attr, value in address.items():
            setattr(instance.address, attr, value)

        instance.address.save()

        return super(ManageProfileSerializer, self).update(instance, validated_data)





# Thanks to Neamar Tucote for this code:
# https://groups.google.com/d/msg/django-rest-framework/abMsDCYbBRg/d2orqUUdTqsJ
class PasswordField(serializers.CharField):
    """ Special field to update a password field. """
    widget = forms.widgets.PasswordInput
    hidden_password_string = '********'

    def to_internal_value(self, value):
        """ Hash if new value sent, else retrieve current password. """
        from django.contrib.auth.hashers import make_password

        if value == self.hidden_password_string or value == '':
            return self.parent.object.password
        else:
            return make_password(value)

    def to_representation(self, value):
        """ Hide hashed-password in API display. """
        return self.hidden_password_string



class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating users. This can only be used for creating
    users (POST) and should not be used for listing,
    editing or viewing users.
    """
    email_confirmation = serializers.EmailField(
        label=_('password_confirmation'), max_length=254, required=False)
    password = PasswordField(required=True, max_length=128)
    username = serializers.CharField(read_only=True)
    jwt_token = serializers.CharField(source='get_jwt_token', read_only=True)
    primary_language = serializers.CharField(required=False)

    @property
    def errors(self):
        errors =  super(UserCreateSerializer, self).errors

        if 'email' in errors and 'email' in self.data:
            user = self.Meta.model.objects.get(email=self.data['email'])

            conflict = {
                'email': user.email,
                'id': user.id
            }

            # We assume if they have a social auth associated then they use
            # it
            if user.social_auth.count() > 0:
                social_auth = user.social_auth.all()[0]
                conflict['provider'] = social_auth.provider
                conflict['type'] = 'social'
            else:
                conflict['type'] = 'email'

            errors[
                settings.REST_FRAMEWORK.get('NON_FIELD_ERRORS_KEY', 'non_field_errors')
            ] = [conflict]

        return errors

    def validate(self, data):
        if 'email_confirmation' in data and data['email'] != data['email_confirmation']:
            raise serializers.ValidationError(_('Email confirmation mismatch'))

        return data

    class Meta:
        model = BB_USER_MODEL
        fields = ('id', 'username', 'first_name', 'last_name', 'email_confirmation',
                  'email', 'password', 'jwt_token', 'primary_language')


def validate_reset_email(email):
    try:
        user = BB_USER_MODEL._default_manager.get(email__iexact=email)
        if not user.is_active or user.password.startswith(UNUSABLE_PASSWORD_PREFIX):
            raise serializers.ValidationError(
                _("That email address doesn't have an associated "
                  "user account. Are you sure you've registered?")
            )
    except BB_USER_MODEL.DoesNotExist:
        raise serializers.ValidationError(
            _("The user account associated with this email "
              "address cannot reset the password.")
        )


class PasswordResetSerializer(serializers.Serializer):
    """
    Password reset request serializer that uses the email validation from the
    Django PasswordResetForm.
    """
    email = serializers.EmailField(required=True, max_length=254, validators=[validate_reset_email])

    class Meta:
        fields = ('email',)


class PasswordSetSerializer(serializers.Serializer):
    """
    We can't use the PasswordField here because it hashes the passwords with
    a salt which means we can't compare the
    two passwords to see if they are the same.
    """
    new_password1 = serializers.CharField(
        required=True, max_length=128)
    new_password2 = serializers.CharField(
        required=True, max_length=128)

    def validate(self, data):
        if data['new_password1'] != data['new_password2']:
            raise serializers.ValidationError(_('The two password fields didn\'t match.'))

        return data

    class Meta:
        fields = ('new_password1', 'new_password2')
