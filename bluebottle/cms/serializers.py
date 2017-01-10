from django.db.models import Sum

from bluebottle.bluebottle_drf2.serializers import ImageSerializer
from bluebottle.members.models import Member
from bluebottle.members.serializers import UserPreviewSerializer
from bluebottle.orders.models import Order
from bluebottle.projects.models import Project
from bluebottle.statistics.statistics import Statistics

from rest_framework import serializers

from bluebottle.cms.models import (
    Stat, StatsContent, ResultPage, QuotesContent, SurveyContent, Quote,
    ProjectImagesContent, ProjectsContent, ShareResultsContent, ProjectsMapContent,
    SupporterTotalContent)
from bluebottle.projects.serializers import ProjectPreviewSerializer, ProjectTinyPreviewSerializer
from bluebottle.surveys.serializers import QuestionSerializer


class RichTextContentSerializer(serializers.Serializer):
    text = serializers.CharField()

    class Meta:
        fields = ('text', 'type')


class MediaFileContentSerializer(serializers.Serializer):
    url = serializers.CharField(source='mediafile.file.url')
    caption = serializers.CharField(source='mediafile.translation.caption')

    def get_url(self, obj):
        return obj.file.url

    class Meta:
        fields = ('url', 'type')


class StatSerializer(serializers.ModelSerializer):
    value = serializers.SerializerMethodField()

    def get_value(self, obj):
        if obj.value:
            return obj.value

        statistics = Statistics(
            start=self.context['start_date'],
            end=self.context['end_date'],
        )

        value = getattr(statistics, obj.type, 0)
        try:
            return {
                'amount': value.amount,
                'currency': str(value.currency)
            }
        except AttributeError:
            return value

    class Meta:
        model = Stat
        fields = ('id', 'title', 'type', 'value')


class StatsContentSerializer(serializers.ModelSerializer):
    stats = StatSerializer(source='stats.stat_set', many=True)
    title = serializers.CharField()
    sub_title = serializers.CharField()

    class Meta:
        model = QuotesContent
        fields = ('id', 'type', 'stats', 'title', 'sub_title')


class QuoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quote
        fields = ('id', 'name', 'quote')


class QuotesContentSerializer(serializers.ModelSerializer):
    quotes = QuoteSerializer(source='quotes.quote_set', many=True)

    class Meta:
        model = QuotesContent
        fields = ('id', 'quotes', 'type', 'title', 'sub_title')


class SurveyContentSerializer(serializers.ModelSerializer):
    answers = QuestionSerializer(many=True, source='survey.visible_questions')
    response_count = serializers.SerializerMethodField()

    def get_response_count(self, obj):
        return obj.survey.response_set.count()

    class Meta:
        model = SurveyContent
        fields = ('id', 'type', 'response_count', 'answers', 'title', 'sub_title')


class ProjectImageSerializer(serializers.ModelSerializer):
    photo = ImageSerializer(source='image')

    class Meta:
        model = Project
        fields = ('id', 'photo', 'title', 'slug')


class ProjectImagesContentSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()

    def get_images(self, obj):
        projects = Project.objects.filter(
            campaign_ended__gte=self.context['start_date'],
            campaign_ended__lte=self.context['end_date'],
            status__slug__in=['done-complete', 'done-incomplete']).order_by('?')

        return ProjectImageSerializer(projects, many=True).to_representation(projects)

    class Meta:
        model = ProjectImagesContent
        fields = ('id', 'type', 'images', 'title', 'sub_title', 'description',
                  'action_text', 'action_link')


class ProjectsMapContentSerializer(serializers.ModelSerializer):
    projects = serializers.SerializerMethodField()

    def get_projects(self, obj):
        projects = Project.objects.filter(
            campaign_ended__gte=self.context['start_date'],
            campaign_ended__lte=self.context['end_date'],
            status__slug__in=['done-complete', 'done-incomplete'])

        return ProjectTinyPreviewSerializer(projects, many=True).to_representation(projects)

    class Meta:
        model = ProjectImagesContent
        fields = ('id', 'type', 'title', 'sub_title', 'projects',)


class ProjectsContentSerializer(serializers.ModelSerializer):
    projects = ProjectPreviewSerializer(many=True, source='projects.projects')

    class Meta:
        model = ProjectsContent
        fields = ('id', 'type', 'title', 'sub_title', 'projects',
                  'action_text', 'action_link')


class ShareResultsContentSerializer(serializers.ModelSerializer):
    statistics = serializers.SerializerMethodField()

    def get_statistics(self, instance):
        stats = Statistics(
            start=self.context['start_date'],
            end=self.context['end_date']
        )

        return {
            'people': stats.people_involved,
            'amount': {
                'amount': stats.donated_total.amount,
                'currency': str(stats.donated_total.currency)
            },
            'hours': stats.time_spent,
            'projects': stats.projects_realized,
            'tasks': stats.tasks_realized,
            'votes': stats.votes_cast,
        }

    class Meta:
        model = ShareResultsContent
        fields = ('id', 'type', 'title', 'sub_title',
                  'statistics', 'share_title', 'share_text')


class CoFinancerSerializer(serializers.Serializer):
    total = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()

    def get_user(self, obj):
        user = Member.objects.get(pk=obj['user'])
        return UserPreviewSerializer(user).to_representation(user)

    def get_id(self, obj):
        return obj['user']

    def get_total(self, obj):
        return {
            'amount': obj['total'],
            'currency': obj['total_currency']
        }

    class Meta:
        fields = ('id', 'user', 'total')


class SupporterTotalContentSerializer(serializers.ModelSerializer):
    supporters = serializers.SerializerMethodField()
    co_financers = serializers.SerializerMethodField()

    def get_supporters(self, instance):
        stats = Statistics(
            start=self.context['start_date'],
            end=self.context['end_date']
        )
        return stats.people_involved

    def get_co_financers(self, instance):
        totals = Order.objects. \
            filter(confirmed__gte=self.context['start_date']). \
            filter(confirmed__lte=self.context['end_date']). \
            filter(status__in=['pending', 'success']). \
            filter(user__is_co_financer=True). \
            values('user', 'total_currency'). \
            annotate(total=Sum('total'))
        return CoFinancerSerializer(totals, many=True).to_representation(totals)

    class Meta:
        model = SupporterTotalContent
        fields = ('id', 'type',
                  'title', 'sub_title', 'co_financer_title',
                  'supporters', 'co_financers')


class BlockSerializer(serializers.Serializer):
    def to_representation(self, obj):
        if isinstance(obj, StatsContent):
            return StatsContentSerializer(obj, context=self.context).to_representation(obj)
        if isinstance(obj, QuotesContent):
            return QuotesContentSerializer(obj, context=self.context).to_representation(obj)
        if isinstance(obj, ProjectImagesContent):
            return ProjectImagesContentSerializer(obj, context=self.context).to_representation(obj)
        if isinstance(obj, SurveyContent):
            return SurveyContentSerializer(obj, context=self.context).to_representation(obj)
        if isinstance(obj, ProjectsContent):
            return ProjectsContentSerializer(obj, context=self.context).to_representation(obj)
        if isinstance(obj, ShareResultsContent):
            return ShareResultsContentSerializer(obj, context=self.context).to_representation(obj)
        if isinstance(obj, ProjectsMapContent):
            return ProjectsMapContentSerializer(obj, context=self.context).to_representation(obj)
        if isinstance(obj, SupporterTotalContent):
            return SupporterTotalContentSerializer(obj, context=self.context).to_representation(obj)


class ResultPageSerializer(serializers.ModelSerializer):
    blocks = BlockSerializer(source='content.contentitems.all.translated', many=True)
    image = ImageSerializer()

    class Meta:
        model = ResultPage
        fields = ('id', 'title', 'slug', 'start_date', 'image',
                  'end_date', 'description', 'blocks')