from rest_framework import serializers
from django.utils.translation import ugettext_lazy as _

from bluebottle.bluebottle_drf2.serializers import (
    PrimaryKeyGenericRelatedField, FileSerializer)
from bluebottle.members.serializers import UserPreviewSerializer
from bluebottle.tasks.models import Task, TaskMember, TaskFile, Skill
from bluebottle.projects.serializers import ProjectPreviewSerializer
from bluebottle.wallposts.serializers import TextWallpostSerializer
from bluebottle.projects.models import Project
from bluebottle.members.models import Member


class TaskPreviewSerializer(serializers.ModelSerializer):
    author = UserPreviewSerializer()
    project = ProjectPreviewSerializer()
    skill = serializers.PrimaryKeyRelatedField(queryset=Skill)

    class Meta:
        model = Task


class BaseTaskMemberSerializer(serializers.ModelSerializer):
    member = UserPreviewSerializer()
    status = serializers.ChoiceField(
        choices=TaskMember.TaskMemberStatuses.choices,
        required=False, default=TaskMember.TaskMemberStatuses.applied)
    motivation = serializers.CharField(required=False)

    class Meta:
        model = TaskMember
        fields = ('id', 'member', 'status', 'created', 'motivation', 'task',
                  'externals')


class TaskFileSerializer(serializers.ModelSerializer):
    author = UserPreviewSerializer()
    file = FileSerializer()

    class Meta:
        model = TaskFile


class BaseTaskSerializer(serializers.ModelSerializer):
    members = BaseTaskMemberSerializer(many=True, read_only=True)
    files = TaskFileSerializer(many=True, read_only=True)
    project = serializers.SlugRelatedField(slug_field='slug',
                                           queryset=Project.objects)
    skill = serializers.PrimaryKeyRelatedField(queryset=Skill.objects)
    author = UserPreviewSerializer()
    status = serializers.ChoiceField(choices=Task.TaskStatuses.choices,
                                     default=Task.TaskStatuses.open)
    time_needed = serializers.DecimalField(min_value=0.0,
                                           max_digits=5,
                                           decimal_places=2)

    def validate(self, data):
        if not data['deadline'] or data['deadline'] > data['project'].deadline:
            raise serializers.ValidationError(
                {'deadline': [_("The deadline must be before the project deadline.")]}
            )
        return data

    class Meta:
        model = Task
        fields = ('id', 'members', 'files', 'project', 'skill',
                  'author', 'status', 'description',
                  'location', 'deadline', 'time_needed', 'title',
                  'people_needed')


class MyTaskPreviewSerializer(serializers.ModelSerializer):
    project = ProjectPreviewSerializer()
    skill = serializers.PrimaryKeyRelatedField(queryset=Skill.objects)

    class Meta:
        model = Task
        fields = ('id', 'title', 'skill', 'project', 'time_needed')


class MyTaskMemberSerializer(BaseTaskMemberSerializer):
    task = MyTaskPreviewSerializer()
    member = serializers.PrimaryKeyRelatedField(queryset=Member.objects)

    class Meta(BaseTaskMemberSerializer.Meta):
        fields = BaseTaskMemberSerializer.Meta.fields + ('time_spent',)


class MyTasksSerializer(BaseTaskSerializer):
    skill = serializers.PrimaryKeyRelatedField(queryset=Skill.objects)

    class Meta:
        model = Task
        fields = ('id', 'title', 'skill', 'project', 'time_needed',
                  'people_needed', 'status', 'deadline', 'description',
                  'location')


# Task Wallpost serializers

class TaskWallpostSerializer(TextWallpostSerializer):
    """ TextWallpostSerializer with task specific customizations. """

    url = serializers.HyperlinkedIdentityField(
        view_name='task-twallpost-detail', lookup_field='pk')
    task = PrimaryKeyGenericRelatedField(Task)

    class Meta(TextWallpostSerializer.Meta):
        # Add the project slug field.
        fields = TextWallpostSerializer.Meta.fields + ('task',)


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ('id', 'name')
