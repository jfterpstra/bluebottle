import socket

from django_fsm import TransitionNotAllowed
from django_tools.middlewares import ThreadLocal
from django.conf import settings
from django.contrib.auth.management import create_permissions
from django.utils.http import urlquote
from django.utils.translation import ugettext as _

from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission

import pygeoip
import logging

from bluebottle.clients import properties


def get_languages():
    return properties.LANGUAGES


class GetTweetMixin(object):
    def get_fb_title(self, **kwargs):
        return self.get_meta_title()

    def get_meta_title(self, **kwargs):
        if hasattr(self, 'country'):
            return u'{name_project} | {country}'.format(
                name_project=self.title,
                country=self.country.name if self.country else '')
        return self.title

    def get_tweet(self, **kwargs):
        """ Build the tweet text for the meta data """
        request = kwargs.get('request')
        if request:
            lang_code = request.LANGUAGE_CODE
        else:
            lang_code = 'en'
        twitter_handle = settings.TWITTER_HANDLES.get(
            lang_code, settings.DEFAULT_TWITTER_HANDLE)

        title = urlquote(self.get_meta_title())

        # {URL} is replaced in Ember to fill in the page url, avoiding the
        # need to provide front-end urls in our Django code.
        tweet = _(u'{title} {{URL}}').format(
            title=title, twitter_handle=twitter_handle)
        return tweet


class StatusDefinition(object):
    """
    Various status definitions for FSM's
    """
    NEW = 'new'
    IN_PROGRESS = 'in_progress'
    PENDING = 'pending'
    CREATED = 'created'
    LOCKED = 'locked'
    PLEDGED = 'pledged'
    SUCCESS = 'success'
    STARTED = 'started'
    CANCELLED = 'cancelled'
    AUTHORIZED = 'authorized'
    SETTLED = 'settled'
    CHARGED_BACK = 'charged_back'
    REFUNDED = 'refunded'
    PAID = 'paid'
    FAILED = 'failed'
    RETRY = 'retry'
    UNKNOWN = 'unknown'


class FSMTransition(object):
    """
    Class mixin to add transition_to method for Django FSM
    """

    def transition_to(self, new_status, save=True):
        # If the new_status is the same as then current then return early
        if self.status == new_status:
            return

        # Lookup the available next transition - from Django FSM
        available_transitions = self.get_available_status_transitions()

        logging.debug("{0} (pk={1}) state changing: '{2}' to '{3}'".format(
            self.__class__.__name__, self.pk, self.status, new_status))

        # Check that the new_status is in the available transitions -
        # created with Django FSM decorator
        for transition in available_transitions:
            if transition.name == new_status:
                transition_method = transition.method

        # Call state transition method
        try:
            instance_method = getattr(self, transition_method.__name__)
            instance_method()
        except UnboundLocalError as e:
            raise TransitionNotAllowed(
                "Can't switch from state '{0}' to state '{1}' for {2}".format(self.status, new_status, self.__class__.__name__))

        if save:
            self.save()

    def refresh_from_db(self):
        """Refreshes this instance from db"""
        new_self = self.__class__.objects.get(pk=self.pk)
        self.__dict__.update(new_self.__dict__)


def get_client_ip(request=None):
    """
    A utility method that returns the client IP for the given request.
    """
    if not request:
        request = ThreadLocal.get_current_request()

    try:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    except AttributeError:
        x_forwarded_for = None

    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        try:
            ip = request.META.get('REMOTE_ADDR')
        except AttributeError:
            ip = None
    return ip


def set_author_editor_ip(request, obj):
    """
    A utility method to set the author, editor and IP address on an
    object based on information in a request.
    """
    if not hasattr(obj, 'author'):
        obj.author = request.user
    else:
        obj.editor = request.user
    obj.ip_address = get_client_ip(request)


def clean_for_hashtag(text):
    """
    Strip non alphanumeric charachters.

    Sometimes, text bits are made up of two parts, sepated by a slash. Split
    those into two tags. Otherwise, join the parts separated by a space.
    """
    tags = []
    bits = text.split('/')
    for bit in bits:
        # keep the alphanumeric bits and capitalize the first letter
        _bits = [_bit.title() for _bit in bit.split() if _bit.isalnum()]
        tag = "".join(_bits)
        tags.append(tag)

    return " #".join(tags)


def import_class(cl):
    d = cl.rfind(".")
    class_name = cl[d + 1:len(cl)]
    m = __import__(cl[0:d], globals(), locals(), [class_name])
    return getattr(m, class_name)


def get_current_host():
    """
    Get the current hostname with protocol
    E.g. http://localhost:8000 or https://bluebottle.org
    """
    request = ThreadLocal.get_current_request()
    if request.is_secure():
        scheme = 'https'
    else:
        scheme = 'http'
    return '{0}://{1}'.format(scheme, request.get_host())


class InvalidIpError(Exception):
    """ Custom exception for an invalid IP address """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def get_country_by_ip(ip_address=None):
    """
    Returns the country associated with the IP address. Uses pygeoip
    library which is based on
    """
    if not ip_address:
        return None

    try:
        socket.inet_aton(ip_address)
    except socket.error:
        raise InvalidIpError("Invalid IP address")

    gi = pygeoip.GeoIP(settings.PROJECT_ROOT + '/GeoIP.dat')
    return gi.country_name_by_addr(ip_address)


def get_country_code_by_ip(ip_address=None):
    """
    Returns the country associated with the IP address. Uses pygeoip
    library which is based on
    the popular Maxmind's GeoIP C API
    """
    if not ip_address:
        return None

    try:
        socket.inet_aton(ip_address)
    except socket.error:
        raise InvalidIpError("Invalid IP address")

    gi = pygeoip.GeoIP(settings.PROJECT_ROOT + '/GeoIP.dat')
    return gi.country_code_by_name(ip_address)


def update_group_permissions(sender, group_perms=None):
    create_permissions(sender, verbosity=False)
    try:
        group_perms = sender.module.models.GROUP_PERMS
        for group_name, permissions in group_perms.items():
            group, _ = Group.objects.get_or_create(name=group_name)
            for perm_codename in permissions['perms']:
                perm = Permission.objects.get(codename=perm_codename)
                group.permissions.add(perm)

            group.save()
    except Exception, e:
        pass

