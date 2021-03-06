from django.contrib.contenttypes.models import ContentType
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from rest_framework import permissions, exceptions

import django_filters

from bluebottle.bluebottle_drf2.pagination import BluebottlePagination
from bluebottle.bluebottle_drf2.permissions import IsAuthorOrReadOnly
from bluebottle.bluebottle_drf2.views import (
    ListCreateAPIView, RetrieveUpdateDeleteAPIView, ListAPIView)
from bluebottle.fundraisers.models import Fundraiser
from bluebottle.tasks.models import Task
from bluebottle.utils.utils import set_author_editor_ip, get_client_ip
from bluebottle.projects.models import Project

from .models import (TextWallpost, MediaWallpost, MediaWallpostPhoto,
                     Wallpost, Reaction)
from .serializers import (TextWallpostSerializer, MediaWallpostSerializer,
                          MediaWallpostPhotoSerializer, ReactionSerializer,
                          WallpostSerializer)
from .permissions import IsConnectedWallpostAuthorOrReadOnly, CanEmailFollowers

from tenant_extras.drf_permissions import TenantConditionalOpenClose


class WallpostFilter(django_filters.FilterSet):
    parent_type = django_filters.CharFilter(name="content_type__name")
    parent_id = django_filters.NumberFilter(name="object_id")

    class Meta:
        model = Wallpost
        fields = ['parent_type', 'parent_id']


class SetAuthorMixin(object):
    def perform_create(self, serializer):
        serializer.save(author=self.request.user, ip_address=get_client_ip(self.request))

    def perform_update(self, serializer):
        serializer.save(editor=self.request.user, ip_address=get_client_ip(self.request))


class WallpostList(ListAPIView):
    queryset = Wallpost.objects.all()
    serializer_class = WallpostSerializer
    pagination_class = BluebottlePagination

    def get_queryset(self, queryset=queryset):
        queryset = super(WallpostList, self).get_queryset()

        # Some custom filtering projects slugs.
        parent_type = self.request.query_params.get('parent_type', None)
        parent_id = self.request.query_params.get('parent_id', None)
        if parent_type == 'project':
            content_type = ContentType.objects.get_for_model(Project)
        else:
            white_listed_apps = ['projects', 'tasks', 'fundraisers']
            content_type = ContentType.objects.filter(
                app_label__in=white_listed_apps).get(model=parent_type)
        queryset = queryset.filter(content_type=content_type)

        if parent_type == 'project' and parent_id:
            try:
                project = Project.objects.get(slug=parent_id)
            except Project.DoesNotExist:
                return Wallpost.objects.none()
            queryset = queryset.filter(object_id=project.id)
        else:
            queryset = queryset.filter(object_id=parent_id)

        queryset = queryset.order_by('-created')
        return queryset


class WallpostPagination(BluebottlePagination):
    page_size = 5


class TextWallpostList(SetAuthorMixin, ListCreateAPIView):
    queryset = TextWallpost.objects.all()
    serializer_class = TextWallpostSerializer
    filter_class = WallpostFilter
    pagination_class = WallpostPagination
    permission_classes = (TenantConditionalOpenClose,
                          IsAuthenticatedOrReadOnly,
                          CanEmailFollowers)

    def get_queryset(self, queryset=None):
        queryset = super(TextWallpostList, self).get_queryset()
        # Some custom filtering projects slugs.
        parent_type = self.request.query_params.get('parent_type', None)
        parent_id = self.request.query_params.get('parent_id', None)
        if parent_type == 'project' and parent_id:
            try:
                project = Project.objects.get(slug=parent_id)
            except Project.DoesNotExist:
                return Wallpost.objects.none()
            queryset = queryset.filter(object_id=project.id)

        queryset = queryset.order_by('-created')
        return queryset


class TextWallpostDetail(SetAuthorMixin, RetrieveUpdateDeleteAPIView):
    queryset = TextWallpost.objects.all()
    serializer_class = TextWallpostSerializer
    permission_classes = (TenantConditionalOpenClose, IsAuthenticatedOrReadOnly)


class MediaWallpostList(TextWallpostList):
    queryset = MediaWallpost.objects.all()
    serializer_class = MediaWallpostSerializer
    filter_class = WallpostFilter
    pagination_class = WallpostPagination


class MediaWallpostDetail(TextWallpostDetail):
    queryset = MediaWallpost.objects.all()
    serializer_class = MediaWallpostSerializer


class WallpostDetail(RetrieveUpdateDeleteAPIView):
    queryset = Wallpost.objects.all()
    serializer_class = WallpostSerializer
    permission_classes = (TenantConditionalOpenClose, IsAuthorOrReadOnly,)
    

class MediaWallpostPhotoPagination(BluebottlePagination):
    page_size = 4


class MediaWallpostPhotoList(SetAuthorMixin, ListCreateAPIView):
    queryset = MediaWallpostPhoto.objects.all()
    serializer_class = MediaWallpostPhotoSerializer
    pagination_class = MediaWallpostPhotoPagination

    def create(self, request, *args, **kwargs):  # FIXME
        """
        Work around browser issues.

        Adding photos to a wallpost works correctly in Chrome. Firefox (at least
        FF 24) sends the ```mediawallpost``` value to Django with the value
        'null', which is then interpreted as a string in Django. This is
        incorrect behaviour, as ```mediawallpost``` is a relation.

        Eventually, this leads to HTTP400 errors, effectively breaking photo
        uploads in FF.

        The quick fix is detecting this incorrect 'null' string in ```request.POST```
        and setting it to an empty string. ```request.POST``` is mutable because
        of the multipart nature.

        NOTE: This is something that should be fixed in the Ember app or maybe even
        Ember itself.
        """
        post = request.POST.get('mediawallpost', False)
        if post and post == u'null':
            request.POST['mediawallpost'] = u''
        return super(MediaWallpostPhotoList, self).create(request, *args,
                                                          **kwargs)


class MediaWallpostPhotoDetail(RetrieveUpdateDeleteAPIView):
    queryset = MediaWallpostPhoto.objects.all()
    serializer_class = MediaWallpostPhotoSerializer
    permission_classes = (TenantConditionalOpenClose, IsAuthorOrReadOnly,
                          IsConnectedWallpostAuthorOrReadOnly)


class ReactionList(SetAuthorMixin, ListCreateAPIView):
    queryset = Reaction.objects.all()
    serializer_class = ReactionSerializer
    permission_classes = (TenantConditionalOpenClose,
                          permissions.IsAuthenticatedOrReadOnly)
    pagination_class = BluebottlePagination
    filter_fields = ('wallpost',)


class ReactionDetail(SetAuthorMixin, RetrieveUpdateDeleteAPIView):
    queryset = Reaction.objects.all()
    serializer_class = ReactionSerializer
    permission_classes = (TenantConditionalOpenClose, IsAuthorOrReadOnly,)
