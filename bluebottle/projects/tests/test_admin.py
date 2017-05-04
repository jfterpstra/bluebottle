import json
import mock

import requests

from django.contrib.admin.sites import AdminSite
from django.contrib import messages
from django.test.client import RequestFactory

from bluebottle.projects.admin import (
    LocationFilter, ProjectReviewerFilter, ProjectAdminForm,
    ReviewerWidget, ProjectAdmin
)
from bluebottle.projects.models import Project
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.geo import LocationFactory
from bluebottle.test.utils import BluebottleTestCase, override_settings

from django.forms.models import modelform_factory


factory = RequestFactory()


PAYOUT_URL = 'http://localhost:8001/payouts/update/'


class MockRequest:
    pass


class MockUser:
    def __init__(self, perms=None):
        self.perms = perms or []

    def has_perm(self, perm):
        return perm in self.perms


@override_settings(PAYOUT_SERVICE={
    'service': 'dorado',
    'url': PAYOUT_URL
})
class TestProjectAdmin(BluebottleTestCase):
    def setUp(self):
        super(TestProjectAdmin, self).setUp()
        self.site = AdminSite()
        self.request_factory = RequestFactory()

        self.init_projects()
        self.project_admin = ProjectAdmin(Project, self.site)
        self.mock_response = requests.Response()
        self.mock_response.status_code = 200

    def test_fieldsets(self):
        request = self.request_factory.get('/')
        request.user = MockUser(['projects.approve_payout'])

        self.assertTrue(
            'payout_status' in self.project_admin.get_fieldsets(request)[0][1]['fields']
        )

    def test_fieldsets_no_permissions(self):
        request = self.request_factory.get('/')
        request.user = MockUser()

        self.assertTrue(
            'payout_status' not in self.project_admin.get_fieldsets(request)
        )

    def test_list_filter(self):
        request = self.request_factory.get('/')
        request.user = MockUser(['projects.approve_payout'])

        self.assertTrue(
            'payout_status' in self.project_admin.get_list_filter(request)
        )

    def test_list_filter_no_permissions(self):
        request = self.request_factory.get('/')
        request.user = MockUser()

        self.assertTrue(
            'payout_status' not in self.project_admin.get_list_filter(request)
        )

    def test_list_display(self):
        request = self.request_factory.get('/')
        request.user = MockUser(['projects.approve_payout'])

        self.assertTrue(
            'payout_status' in self.project_admin.get_list_display(request)
        )

    def test_list_display_no_permissions(self):
        request = MockRequest()
        request.user = MockUser()

        self.assertTrue(
            'payout_status' not in self.project_admin.get_list_display(request)
        )

    def test_mark_payout_as_approved(self):
        request = self.request_factory.post('/')
        request.user = MockUser(['projects.approve_payout'])

        project = ProjectFactory.create(payout_status='needs_approval')

        with mock.patch('requests.post', return_value=self.mock_response) as request_mock:
            self.project_admin.approve_payout(request, project.id)

        request_mock.assert_called_with(
            PAYOUT_URL, {'project_id': project.id, 'tenant': 'test'}
        )

    def test_mark_payout_as_approved_validation_error(self):
        request = self.request_factory.post('/')
        request.user = MockUser(['projects.approve_payout'])

        project = ProjectFactory.create(payout_status='needs_approval')

        self.mock_response.status_code = 400
        self.mock_response._content = json.dumps({'errors': {'name': ['This field is required']}})
        with mock.patch('requests.post', return_value=self.mock_response) as request_mock:
            with mock.patch.object(self.project_admin, 'message_user') as message_mock:
                self.project_admin.approve_payout(request, project.id)

        request_mock.assert_called_with(
            PAYOUT_URL, {'project_id': project.id, 'tenant': 'test'}
        )

        message_mock.assert_called_with(
            request, 'Account details: name, this field is required.', level=messages.ERROR
        )

    def test_mark_payout_as_approved_internal_server_error(self):
        request = self.request_factory.post('/')
        request.user = MockUser(['projects.approve_payout'])

        project = ProjectFactory.create(payout_status='needs_approval')

        self.mock_response.status_code = 500
        self.mock_response._content = 'Internal Server Error'

        with mock.patch('requests.post', return_value=self.mock_response) as request_mock:
            with mock.patch.object(self.project_admin, 'message_user') as message_mock:
                self.project_admin.approve_payout(request, project.id)

        request_mock.assert_called_with(
            PAYOUT_URL, {'project_id': project.id, 'tenant': 'test'}
        )

        message_mock.assert_called_with(
            request, 'Failed to approve payout: Internal Server Error', level=messages.ERROR
        )

    def test_mark_payout_as_approved_connection_error(self):
        request = self.request_factory.post('/')
        request.user = MockUser(['projects.approve_payout'])

        project = ProjectFactory.create(payout_status='needs_approval')
        exception = requests.ConnectionError('Host not found')

        with mock.patch('requests.post', side_effect=exception) as request_mock:
            with mock.patch.object(self.project_admin, 'message_user') as message_mock:
                self.project_admin.approve_payout(request, project.id)

        request_mock.assert_called_with(
            PAYOUT_URL, {'project_id': project.id, 'tenant': 'test'}
        )

        message_mock.assert_called_with(
            request, 'Failed to approve payout: Host not found', level=messages.ERROR
        )

    def test_mark_payout_as_approved_no_permissions(self):
        request = self.request_factory.post('/')
        request.user = MockUser()

        with mock.patch('requests.post', return_value=self.mock_response) as request_mock:
            project = ProjectFactory.create(payout_status='needs_approval')

        response = self.project_admin.approve_payout(request, project.id)
        self.assertEqual(response.status_code, 403)
        request_mock.assert_not_called()

    def test_mark_payout_as_approved_wrong_status(self):
        request = self.request_factory.post('/')
        request.user = MockUser(['projects.approve_payout'])

        project = ProjectFactory.create(payout_status='done')
        with mock.patch('requests.post', return_value=self.mock_response) as request_mock:
            with mock.patch.object(self.project_admin, 'message_user') as message_mock:
                self.project_admin.approve_payout(request, project.id)

        self.assertEqual(
            Project.objects.get(id=project.id).payout_status, 'done'
        )
        request_mock.assert_not_called()
        message_mock.assert_called()

    def test_read_only_status_after_payout_approved(self):
        request = self.request_factory.post('/')
        request.user = MockUser(['projects.approve_payout'])

        project = ProjectFactory.create(payout_status='needs_approval')

        # Project status should be editable
        self.assertFalse(
            'status' in self.project_admin.get_readonly_fields(request, obj=project)
        )

        def side_effect(*args, **kwargs):
            project.payout_status = 'approved'
            project.save()
            return self.mock_response

        with mock.patch('requests.post', side_effect=side_effect):
            self.project_admin.approve_payout(request, project.id)

        project = Project.objects.get(id=project.id)

        # Project status should be readonly after payout has been approved
        self.assertTrue(
            'status' in self.project_admin.get_readonly_fields(request, obj=project)
        )


class LocationFilterTest(BluebottleTestCase):
    """
    Test project admin location filter
    """

    def setUp(self):
        super(LocationFilterTest, self).setUp()
        self.init_projects()

        amsterdam = LocationFactory.create(name='Amsterdam')
        rotterdam = LocationFactory.create(name='Rotterdam')
        durgerdam = LocationFactory.create(name='Durgerdam')
        self.locations = [amsterdam, rotterdam, durgerdam]

        self.user = BlueBottleUserFactory.create(location=amsterdam)
        self.amsterdam_project = ProjectFactory.create(
            title='Project in Amsterdam',
            location=amsterdam
        )
        ProjectFactory.create(
            title='Project in Rotterdam',
            location=rotterdam
        )
        ProjectFactory.create(
            title='Project in Durgerdam',
            location=durgerdam
        )
        self.admin = ProjectAdmin(Project, AdminSite())

        self.filter = LocationFilter(None, {'location': amsterdam.pk}, Project, self.admin)

    def testLookup(self):
        request = factory.get('/', user=None)

        lookups = self.filter.lookups(request, self.admin)
        self.assertEqual(
            set(location.name for location in self.locations),
            set(lookup[1] for lookup in lookups)
        )

    def testLookupUser(self):
        request = factory.get('/')
        request.user = self.user
        lookups = self.filter.lookups(request, self.admin)

        self.assertEqual(len(lookups), 4)
        self.assertEqual(
            lookups[0],
            (request.user.location.id, u'My location (Amsterdam)')
        )

    def test_filter(self):
        queryset = self.filter.queryset(None, Project.objects.all())
        self.assertEqual(queryset.get(), self.amsterdam_project)


class ProjectReviewerFilterTest(BluebottleTestCase):
    """
    Test project reviewer filter
    """

    def setUp(self):
        super(ProjectReviewerFilterTest, self).setUp()
        self.init_projects()

        self.user = BlueBottleUserFactory.create()
        self.project_with_reviewer = ProjectFactory.create(
            reviewer=self.user
        )
        self.project = ProjectFactory.create(
        )

        self.request = factory.get('/')
        self.request.user = self.user
        self.admin = ProjectAdmin(Project, AdminSite())

    def test_filter(self):
        filter = ProjectReviewerFilter(None, {'reviewer': True}, Project, self.admin)
        queryset = filter.queryset(self.request, Project.objects.all())
        self.assertEqual(queryset.get(), self.project_with_reviewer)

    def test_filter_false(self):
        filter = ProjectReviewerFilter(None, {'reviewer': False}, Project, self.admin)
        queryset = filter.queryset(self.request, Project.objects.all())
        self.assertEqual(len(queryset), len(Project.objects.all()))


class ProjectAdminFormTest(BluebottleTestCase):
    def setUp(self):
        super(ProjectAdminFormTest, self).setUp()
        self.init_projects()
        self.form = modelform_factory(Project, ProjectAdminForm, exclude=[])()

    def test_reviewer_field(self):
        widget = self.form.fields['reviewer'].widget
        self.assertTrue(
            isinstance(widget, ReviewerWidget)
        )
        parameters = widget.url_parameters()
        self.assertTrue(parameters['is_staff'], True)
