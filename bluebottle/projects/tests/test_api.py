from datetime import timedelta, datetime
import json
from random import randint

from django.test import RequestFactory
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.test.utils import override_settings

from moneyed import Money

from rest_framework import status
from rest_framework.status import HTTP_200_OK

from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.test.factory_models.categories import CategoryFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.geo import CountryFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.organizations import OrganizationFactory
from bluebottle.test.factory_models.projects import ProjectFactory, ProjectDocumentFactory
from bluebottle.test.factory_models.tasks import (
    TaskFactory, TaskMemberFactory, SkillFactory
)
from bluebottle.test.factory_models.votes import VoteFactory
from bluebottle.test.factory_models.wallposts import (
    MediaWallpostFactory, MediaWallpostPhotoFactory,
    TextWallpostFactory)
from bluebottle.test.utils import BluebottleTestCase

from ..models import Project


# RequestFactory used for integration tests.
factory = RequestFactory()


class ProjectEndpointTestCase(BluebottleTestCase):
    """
    Integration tests for the Project API.
    """

    def setUp(self):
        super(ProjectEndpointTestCase, self).setUp()
        self.init_projects()

        """
        Create 26 Project instances.
        """
        self.user = BlueBottleUserFactory.create()
        self.user_token = "JWT {0}".format(self.user.get_jwt_token())

        organization = OrganizationFactory.create()
        organization.save()

        self.campaign_phase = ProjectPhase.objects.get(slug='campaign')
        self.plan_phase = ProjectPhase.objects.get(slug='done-complete')
        self.projects = []

        for char in 'abcdefghijklmnopqrstuvwxyz':
            # Put half of the projects in the campaign phase.
            if ord(char) % 2 == 1:
                project = ProjectFactory.create(title=char * 3, slug=char * 3,
                                                status=self.campaign_phase,
                                                amount_asked=0,
                                                amount_needed=30,
                                                organization=organization)
                project.save()
            else:
                project = ProjectFactory.create(title=char * 3, slug=char * 3,
                                                status=self.plan_phase,
                                                organization=organization)

                task = TaskFactory.create(project=project)
                project.save()
                task.save()

            self.projects.append(project)

        self.projects_preview_url = reverse('project_preview_list')
        self.projects_url = reverse('project_list')
        self.manage_projects_url = reverse('project_manage_list')


class ProjectApiIntegrationTest(ProjectEndpointTestCase):
    def test_project_list_view(self):
        """
        Tests for Project List view. These basic tests are here because Project
        is the first API to use DRF2. Not all APIs need thorough integration
        testing like this.
        """

        # Basic test of DRF2.
        response = self.client.get(self.projects_preview_url)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.data['count'], 26)
        self.assertEquals(len(response.data['results']), 8)
        self.assertNotEquals(response.data['next'], None)
        self.assertEquals(response.data['previous'], None)

    def test_project_list_view_query_filters(self):
        """
        Tests for Project List view with filters. These basic tests are here
        because Project is the first API to use DRF2. Not all APIs need
        thorough integration testing like this.
        """

        # Tests that the phase filter works.
        response = self.client.get(
            '%s?status=%s' % (self.projects_preview_url, self.plan_phase.slug))
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.data['count'], 13)
        self.assertEquals(len(response.data['results']), 8)

        # Tests that the phase filter works.
        response = self.client.get(self.projects_preview_url + '?project_type=volunteering')
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.data['count'], 13)
        self.assertEquals(len(response.data['results']), 8)

        # Test that ordering works
        response = self.client.get(self.projects_preview_url + '?ordering=newest')
        self.assertEquals(response.status_code, 200)
        response = self.client.get(self.projects_preview_url + '?ordering=title')
        self.assertEquals(response.status_code, 200)
        response = self.client.get(self.projects_preview_url + '?ordering=deadline')
        self.assertEquals(response.status_code, 200)
        response = self.client.get(self.projects_preview_url + '?ordering=amount_needed')
        self.assertEquals(response.status_code, 200)
        response = self.client.get(self.projects_preview_url + '?ordering=popularity')
        self.assertEquals(response.status_code, 200)

        # Test that combination of arguments works
        response = self.client.get(
            self.projects_url + '?ordering=deadline&phase=campaign&country=101')
        self.assertEquals(response.status_code, 200)

    def test_project_detail_no_expertise(self):
        for project in self.projects:
            for task in project.task_set.all():
                task.skill = None
                task.save()

        response = self.client.get(self.projects_preview_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)

        self.assertEqual(data['count'], 26)

        for item in data['results']:
            self.assertEqual(item['skills'], [])

    def test_project_detail_expertise(self):
        for project in self.projects:
            TaskFactory.create(project=project)
            TaskFactory.create(project=project)

        response = self.client.get(self.projects_preview_url)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data['count'], 26)

        for item in data['results']:
            project = Project.objects.get(slug=item['id'])
            for task in project.task_set.all():
                self.assertTrue(
                    task.skill.id in item['skills']
                )

    def test_project_list_filter_expertise(self):
        skill = SkillFactory.create(name='test skill')
        for project in self.projects[:3]:
            TaskFactory.create(project=project, skill=skill)
            TaskFactory.create(project=project, skill=skill)

        response = self.client.get(self.projects_preview_url + '?skill={}'.format(skill.pk))
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data['count'], 3)

        for item in data['results']:
            project = Project.objects.get(slug=item['id'])
            self.assertTrue(
                skill in [task.skill for task in project.task_set.all()]
            )

    def test_project_order_amount_needed(self):
        for project in Project.objects.all():
            project.amount_needed = Money(randint(0, int(project.amount_asked.amount)), 'EUR')
            project.save()

        response = self.client.get(self.projects_preview_url + '?ordering=amount_needed')
        amounts = [project['amount_needed']['amount'] for project in response.data['results']]

        self.assertEqual(amounts, sorted(amounts))

    def test_project_detail_view(self):
        """ Tests retrieving a project detail from the API. """

        # Get the list of projects.
        response = self.client.get(self.projects_url)
        self.assertEquals(response.status_code, status.HTTP_200_OK)

        # Test retrieving the first project detail from the list.
        project = response.data['results'][0]
        response = self.client.get(self.projects_url + str(project['id']))

        owner = response.data['owner']
        self.assertEquals(owner['project_count'], 1)
        self.assertEquals(owner['task_count'], 0)
        self.assertEquals(owner['donation_count'], 0)
        self.assertTrue(owner.get('email', None) is None)
        self.assertEquals(response.status_code, status.HTTP_200_OK)

    def test_project_detail_view_bank_details(self):
        """ Test that the correct bank details are returned for a project """

        country = CountryFactory.create()

        project = ProjectFactory.create(title='test project',
                                        owner=self.user,
                                        account_holder_name='test name',
                                        account_holder_address='test address',
                                        account_holder_postal_code='12345AC',
                                        account_holder_city='Amsterdam',
                                        account_holder_country=country,
                                        account_number='NL18ABNA0484869868',
                                        account_bank_country=country
                                        )
        project.save()

        response = self.client.get(self.manage_projects_url + str(project.slug),
                                   token=self.user_token)

        self.assertEquals(response.status_code, status.HTTP_200_OK, response)
        self.assertEquals(response.data['title'], 'test project')
        self.assertEquals(response.data['account_number'], 'NL18ABNA0484869868')
        self.assertEquals(response.data['account_bic'], 'ABNANL2A')
        self.assertEquals(response.data['account_bank_country'], country.id)

        self.assertEquals(response.data['account_holder_name'], 'test name')
        self.assertEquals(response.data['account_holder_address'],
                          'test address')
        self.assertEquals(response.data['account_holder_postal_code'],
                          '12345AC')
        self.assertEquals(response.data['account_holder_city'], 'Amsterdam')
        self.assertEquals(response.data['account_holder_country'], country.id)

    def test_project_get_vote_count(self):
        """ Tests retrieving a project's vote count from the API. """

        # Get the list of projects.
        response = self.client.get(self.projects_url)
        self.assertEquals(response.status_code, status.HTTP_200_OK)

        # Test retrieving the first project detail from the list.
        project = response.data['results'][0]
        project_object = Project.objects.get(slug=str(project['id']))

        # Create votes
        VoteFactory.create(project=project_object, voter=self.user)

        user2 = BlueBottleUserFactory.create()
        VoteFactory.create(project=project_object, voter=user2)

        # Test retrieving the first project detail from the list.
        response = self.client.get(self.projects_url + str(project['id']))
        self.assertEquals(response.status_code, status.HTTP_200_OK)

        self.assertEquals(response.data['vote_count'], 2)


class ProjectDateSearchTestCase(BluebottleTestCase):
    """
    Integration tests for the Project API.
    """

    def setUp(self):
        super(ProjectDateSearchTestCase, self).setUp()
        self.init_projects()

        campaign_phase = ProjectPhase.objects.get(slug='campaign')

        self.user = BlueBottleUserFactory.create()
        self.user_token = "JWT {0}".format(self.user.get_jwt_token())

        self.projects_preview_url = reverse('project_preview_list')

        self.projects = [
            ProjectFactory.create(status=campaign_phase) for _index in range(0, 10)
        ]

        for project in self.projects[:4]:
            TaskFactory.create(
                project=project,
                type='ongoing',
                deadline=datetime(2017, 1, 20, tzinfo=timezone.get_current_timezone())
            )

        for project in self.projects[3:6]:
            TaskFactory.create(
                project=project,
                type='event',
                deadline=datetime(2017, 1, 10, tzinfo=timezone.get_current_timezone())
            )

    def test_project_list_filter_date(self):
        response = self.client.get(
            self.projects_preview_url + '?start={}'.format('2017-01-10')
        )
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data['count'], 6)

    def test_project_list_filter_date_end(self):
        response = self.client.get(
            self.projects_preview_url + '?start={}&end={}'.format('2017-01-5', '2017-01-25')
        )
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data['count'], 6)

    def test_project_list_filter_date_ongoing(self):
        response = self.client.get(
            self.projects_preview_url + '?start={}'.format('2017-01-20')
        )
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data['count'], 4)

        for item in data['results']:
            project = Project.objects.get(slug=item['id'])
            self.assertTrue(
                'ongoing' in [task.type for task in project.task_set.all()]
            )

    def test_project_list_filter_date_ongoing_end(self):
        response = self.client.get(
            self.projects_preview_url + '?start={}&end={}'.format('2017-01-15', '2017-01-25')
        )
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data['count'], 4)

        for item in data['results']:
            project = Project.objects.get(slug=item['id'])
            self.assertTrue(
                'ongoing' in [task.type for task in project.task_set.all()]
            )

    def test_project_list_filter_date_passed(self):
        self.projects[-1].task_set.all().update(location=None)
        response = self.client.get(
            self.projects_preview_url + '?start={}'.format('2017-01-21')
        )
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data['count'], 0)

    def test_project_list_filter_anywhere(self):
        self.projects[1].task_set.all().update(location=None)

        response = self.client.get(
            self.projects_preview_url + '?anywhere=1'
        )
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data['count'], 1)


class ProjectManageApiIntegrationTest(BluebottleTestCase):
    """
    Integration tests for the Project API.
    """

    def setUp(self):
        super(ProjectManageApiIntegrationTest, self).setUp()

        self.some_user = BlueBottleUserFactory.create()
        self.some_user_token = "JWT {0}".format(self.some_user.get_jwt_token())

        self.another_user = BlueBottleUserFactory.create()
        self.another_user_token = "JWT {0}".format(
            self.another_user.get_jwt_token())

        self.init_projects()

        self.phase_plan_new = ProjectPhase.objects.get(slug='plan-new')
        self.phase_submitted = ProjectPhase.objects.get(slug='plan-submitted')
        self.phase_campaign = ProjectPhase.objects.get(slug='campaign')

        self.manage_projects_url = reverse('project_manage_list')
        self.manage_budget_lines_url = reverse('project-budgetline-list')
        self.manage_project_document_url = reverse('manage-project-document-list')
        self.some_photo = './bluebottle/projects/test_images/upload.png'

    def test_project_create(self):
        """
        Tests for Project Create
        """

        # Check that a new user doesn't have any projects to manage
        response = self.client.get(
            self.manage_projects_url, token=self.some_user_token)
        self.assertEquals(response.data['count'], 0)

        # Let's throw a pitch (create a project really)
        response = self.client.post(self.manage_projects_url,
                                    {'title': 'This is my smart idea', 'story': ''},
                                    token=self.some_user_token)
        self.assertEquals(
            response.status_code, status.HTTP_201_CREATED, response)
        self.assertEquals(response.data['title'], 'This is my smart idea')

        # Check that it's there, in pitch phase, has got a pitch but no plan
        # yet.
        response = self.client.get(
            self.manage_projects_url, token=self.some_user_token)
        self.assertEquals(response.data['count'], 1)
        self.assertEquals(
            response.data['results'][0]['status'], self.phase_plan_new.id)
        self.assertEquals(response.data['results'][0]['pitch'], '')

        # Get the project
        project_id = response.data['results'][0]['id']
        response = self.client.get(
            self.manage_projects_url + str(project_id),
            token=self.some_user_token)
        self.assertEquals(response.status_code, status.HTTP_200_OK, response)
        self.assertEquals(response.data['title'], 'This is my smart idea')

        # Let's check that another user can't get this pitch
        response = self.client.get(reverse('project_manage_detail',
                                           kwargs={'slug': project_id}),
                                   token=self.another_user_token)
        self.assertEquals(
            response.status_code, status.HTTP_403_FORBIDDEN, response)

        # Let's create a pitch for this other user
        response = self.client.post(self.manage_projects_url,
                                    {'title': 'My idea is way smarter!'},
                                    token=self.another_user_token)
        project_url = reverse(
            'project_manage_detail', kwargs={'slug': response.data['slug']})
        self.assertEquals(response.data['title'], 'My idea is way smarter!')

        # Add some values to this project
        project_data = {
            'title': 'My idea is way smarter!',
            'pitch': 'Lorem ipsum, bla bla ',
            'description': 'Some more text',
            'amount_asked': 1000
        }
        response = self.client.put(project_url, project_data,
                                   token=self.another_user_token)
        self.assertEquals(response.status_code, status.HTTP_200_OK, response)

        # Let's put a project_type on it
        project_data['project_type'] = 'funding'
        self.client.put(project_url, project_data, token=self.some_user_token)
        response = self.client.put(project_url, project_data,
                                   token=self.another_user_token)
        self.assertEquals(response.status_code, status.HTTP_200_OK, response)
        self.assertEquals(response.data['project_type'], 'funding')

        # Back to the previous pitch. Try to cheat and put it to status
        # approved.
        project_data['status'] = self.phase_campaign.id
        response = self.client.put(project_url, project_data,
                                   token=self.another_user_token)
        self.assertEqual(response.status_code,
                         status.HTTP_400_BAD_REQUEST, response.data)
        self.assertEquals(response.data['status'][0],
                          'You can not change the project state.',
                          'status change should not be possible')

        # Ok, let's try to submit it. We have to submit all previous data again
        # too.
        project_data['status'] = self.phase_submitted.id
        response = self.client.put(project_url, project_data,
                                   token=self.another_user_token)
        self.assertEquals(response.status_code, status.HTTP_200_OK, response)
        self.assertEquals(response.data['status'], self.phase_submitted.id)

        # Changing the project should be impossible now
        # previous value
        project_data['slug'] = 'a-new-slug-should-not-be-possible'
        response_2 = self.client.put(project_url, project_data,
                                     token=self.another_user_token)
        self.assertEquals(response_2.data['detail'],
                          'You do not have permission to perform this action.')
        self.assertEquals(response_2.status_code, 403)

        # Set the project to plan phase from the backend
        project = Project.objects.get(slug=response.data.get('slug'))
        project.status = self.phase_campaign
        project.save()

        # Let's look at the project again. It should be in campaign phase now.
        response = self.client.get(project_url, token=self.another_user_token)
        self.assertEquals(response.status_code, status.HTTP_200_OK, response)
        self.assertEquals(response.data['status'], self.phase_campaign.id)

        # Trying to create a project with the same title should result in an
        # error.
        response = self.client.post(self.manage_projects_url,
                                    {'title': 'This is my smart idea'},
                                    token=self.another_user_token)
        self.assertEqual(response.status_code,
                         status.HTTP_400_BAD_REQUEST,
                         response.data)
        self.assertEqual(response.data['title'][0],
                         u'Project with this title already exists.')

        # Anonymous user should not be able to find this project through
        # management API.
        response = self.client.get(project_url)
        self.assertEquals(
            response.status_code, status.HTTP_401_UNAUTHORIZED, response)

        # Also it should not be visible by the first user.
        response = self.client.get(project_url, token=self.some_user_token)
        self.assertEquals(
            response.status_code, status.HTTP_403_FORBIDDEN, response)

    @override_settings(PROJECT_CREATE_TYPES=['sourcing'])
    def test_project_type(self):
        # Add some values to this project
        project_data = {
            'title': 'My idea is way smarter!',
            'pitch': 'Lorem ipsum, bla bla ',
            'description': 'Some more text',
            'amount_asked': 1000
        }

        response = self.client.post(self.manage_projects_url,
                                    project_data,
                                    token=self.another_user_token)
        self.assertEquals(response.status_code, status.HTTP_201_CREATED, response)
        self.assertEquals(response.data['project_type'], 'sourcing',
                          'Project should have a default project_type')

    @override_settings(PROJECT_CREATE_TYPES=['sourcing'])
    def test_project_type_defined(self):
        # Add some values to this project
        project_data = {
            'title': 'My idea is way smarter!',
            'pitch': 'Lorem ipsum, bla bla ',
            'description': 'Some more text',
            'amount_asked': 1000,
            'project_type': 'funding'
        }

        response = self.client.post(self.manage_projects_url,
                                    project_data,
                                    token=self.another_user_token)
        self.assertEquals(response.status_code, status.HTTP_201_CREATED, response)
        self.assertEquals(response.data['project_type'], 'funding',
                          'Project should use project_type if defined')

    def test_project_document_upload(self):
        project = ProjectFactory.create(title="testproject",
                                        slug="testproject",
                                        owner=self.some_user,
                                        status=ProjectPhase.objects.get(
                                            slug='plan-new'))

        photo_file = open(self.some_photo, mode='rb')
        response = self.client.post(self.manage_project_document_url,
                                    {'file': photo_file, 'project': project.slug},
                                    token=self.some_user_token, format='multipart')

        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)

        self.assertTrue(
            data['file']['url'].startswith('/downloads/project/document')
        )

    def test_project_document_download(self):
        document = ProjectDocumentFactory.create(
            author=self.some_user,
            file='private/projects/documents/test.jpg'
        )
        file_url = reverse('project-document-file', args=[document.pk])
        response = self.client.get(file_url)

        self.assertEqual(response.status_code, 403)

    def test_project_document_download_author(self):
        document = ProjectDocumentFactory.create(
            author=self.some_user,
            file='private/projects/documents/test.jpg'
        )
        file_url = reverse('project-document-file', args=[document.pk])
        response = self.client.get(file_url, token=self.some_user_token)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['X-Accel-Redirect'], '/media/private/projects/documents/test.jpg'
        )

    def test_project_document_download_non_author(self):
        document = ProjectDocumentFactory.create(
            author=self.some_user,
            file='private/projects/documents/test.jpg'
        )
        file_url = reverse('project-document-file', args=[document.pk])
        response = self.client.get(file_url, token=self.another_user_token)

        self.assertEqual(response.status_code, 403)

    def test_project_document_staff_session_user(self):
        self.another_user.is_staff = True
        self.another_user.save()

        document = ProjectDocumentFactory.create(
            author=self.some_user,
            file='private/projects/documents/test.jpg'
        )
        file_url = reverse('project-document-file', args=[document.pk])
        self.client.force_login(self.another_user)
        response = self.client.get(file_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['X-Accel-Redirect'], '/media/private/projects/documents/test.jpg'
        )

    def test_project_document_non_staff_session_user(self):
        document = ProjectDocumentFactory.create(
            author=self.some_user,
            file='private/projects/documents/test.jpg'
        )
        file_url = reverse('project-document-file', args=[document.pk])
        self.client.force_login(self.another_user)
        response = self.client.get(file_url)

        self.assertEqual(response.status_code, 403)

    def test_create_project_contains_empty_bank_details(self):
        """ Create project with bank details. Ensure they are returned """
        project_data = {
            'title': 'Project with bank details'
        }

        response = self.client.post(self.manage_projects_url, project_data,
                                    token=self.some_user_token)

        self.assertEquals(response.status_code,
                          status.HTTP_201_CREATED,
                          response)

        bank_detail_fields = ['account_number', 'account_bic',
                              'account_bank_country']

        for field in bank_detail_fields:
            self.assertIn(field, response.data)

    def test_project_create_invalid_image(self):
        """
        Tests for Project Create
        """

        # Check that a new user doesn't have any projects to manage
        response = self.client.get(
            self.manage_projects_url, token=self.some_user_token)
        self.assertEquals(response.data['count'], 0)

        # Let's throw a pitch (create a project really)
        image_filename = './bluebottle/projects/test_images/circle.eps'
        image = open(image_filename, mode='rb')

        response = self.client.post(self.manage_projects_url,
                                    {
                                        'title': 'This is my smart idea',
                                        'image': image
                                    },
                                    token=self.some_user_token,
                                    format='multipart')
        self.assertContains(
            response,
            "Upload a valid image",
            status_code=400
        )

    def test_project_create_amounts(self):
        """
        Tests for Project Create
        """
        amount_asked = {'currency': 'EUR', 'amount': 100}
        response = self.client.post(self.manage_projects_url,
                                    {
                                        'title': 'This is my smart idea',
                                        'amount_asked': amount_asked
                                    },
                                    token=self.some_user_token
                                    )
        self.assertEqual(response.data['amount_asked'], amount_asked)
        self.assertEqual(response.data['currencies'], ['EUR'])

    def test_set_bank_details(self):
        """ Set bank details in new project """

        country = CountryFactory.create()

        project_data = {
            'title': 'Project with bank details',
            'account_number': 'NL18ABNA0484869868',
            'account_bic': 'ABNANL2A',
            'account_bank_country': country.pk,
            'account_holder_name': 'blabla',
            'account_holder_address': 'howdy',
            'account_holder_postal_code': '12334',
            'account_holder_city': 'yada yada',
            'account_holder_country': country.pk
        }

        response = self.client.post(self.manage_projects_url, project_data,
                                    token=self.some_user_token)

        self.assertEquals(response.status_code,
                          status.HTTP_201_CREATED,
                          response)

        bank_detail_fields = ['account_number', 'account_bic',
                              'account_bank_country',
                              'account_holder_name', 'account_holder_address',
                              'account_holder_postal_code',
                              'account_holder_city',
                              'account_holder_country']

        for field in bank_detail_fields:
            self.assertEqual(response.data[field], project_data[field])

    def test_set_invalid_iban(self):
        """ Set invalid iban bank detail """

        project_data = {
            'title': 'Project with bank details',
            'account_number': 'NL18ABNA0484fesewf869868',
        }

        response = self.client.post(self.manage_projects_url, project_data,
                                    token=self.some_user_token)

        # This will just pass now because we removed Iban check
        # because the field can hold a non-Iban account too.
        self.assertEquals(response.status_code,
                          status.HTTP_400_BAD_REQUEST)
        self.assertEquals(json.loads(response.content)['account_number'][0],
                          'NL IBANs must contain 18 characters.')

    def test_set_invalid_bic(self):
        """ Set invalid bic bank detail """

        project_data = {
            'title': 'Project with bank details',
            'account_bic': 'vlkengkewngklw',
        }

        response = self.client.post(self.manage_projects_url, project_data,
                                    token=self.some_user_token)

        self.assertEquals(response.status_code,
                          status.HTTP_400_BAD_REQUEST)
        self.assertEquals(json.loads(response.content)['account_bic'][0],
                          u'BIC codes have either 8 or 11 characters.')

    def test_skip_iban_validation(self):
        """ The iban validation should be skipped for other account formats """

        project_data = {
            'title': 'Project with bank details',
            'account_number': '56105910810182',
        }

        response = self.client.post(self.manage_projects_url, project_data,
                                    token=self.some_user_token)

        self.assertEquals(response.status_code,
                          status.HTTP_201_CREATED)

    def test_project_budgetlines_crud(self):
        project_data = {"title": "Some project with a goal & budget"}
        response = self.client.post(self.manage_projects_url, project_data,
                                    token=self.some_user_token)
        self.assertEquals(response.data['title'], project_data['title'])
        project_id = response.data['id']
        project_url = '{0}{1}'.format(self.manage_projects_url, project_id)

        # Check that there aren't any budgetlines
        self.assertEquals(response.data['budget_lines'], [])

        budget = [
            {'project': project_id, 'description': 'Stuff', 'amount': 800},
            {'project': project_id, 'description': 'Things', 'amount': 1200},
            {'project': project_id,
             'description': 'Random produce', 'amount': 170}
        ]

        for line in budget:
            response = self.client.post(
                self.manage_budget_lines_url, line, token=self.some_user_token)
            self.assertEquals(
                response.status_code, status.HTTP_201_CREATED, response)

        # We should have 3 budget lines by now
        response = self.client.get(project_url, token=self.some_user_token)
        self.assertEquals(len(response.data['budget_lines']), 3)

        # Let's change a budget_line
        budget_line = response.data['budget_lines'][0]
        budget_line['amount'] = 350
        budget_line_url = "{0}{1}".format(
            self.manage_budget_lines_url, budget_line['id'])
        response = self.client.put(budget_line_url, budget_line,
                                   token=self.some_user_token)
        self.assertEquals(response.status_code, status.HTTP_200_OK, response)
        self.assertEquals(response.data['amount']['amount'], 350.00)
        self.assertEquals(response.data['amount']['currency'], 'EUR')

        # Now remove that line
        response = self.client.delete(
            budget_line_url, token=self.some_user_token)
        self.assertEquals(
            response.status_code, status.HTTP_204_NO_CONTENT, response)

        # Should have 2  budget lines now
        response = self.client.get(project_url, token=self.some_user_token)
        self.assertEquals(len(response.data['budget_lines']), 2)

        # Login as another user and try to add a budget line to this project.
        response = self.client.post(self.manage_budget_lines_url,
                                    line, token=self.another_user_token)
        self.assertEquals(response.status_code,
                          status.HTTP_403_FORBIDDEN,
                          response)


class ProjectStoryXssTest(BluebottleTestCase):
    def setUp(self):
        super(ProjectStoryXssTest, self).setUp()

        self.init_projects()
        self.some_user = BlueBottleUserFactory.create()

    def test_unsafe_story(self):
        story = '''
        <p onmouseover=\"alert('Persistent_XSS');\"></p>
        <br size="&{alert('Injected')}">
        <div style="background-image: url(javascript:alert('Injected'))">
        <script>alert('Injected!');</script>
        '''

        project = ProjectFactory.create(title="testproject",
                                        slug="testproject",
                                        story=story,
                                        owner=self.some_user,
                                        status=ProjectPhase.objects.get(
                                            slug='campaign'))

        response = self.client.get(reverse('project_detail',
                                           args=[project.slug]))
        escaped_story = '''
        <p></p>
        <br>
        &lt;div style="background-image: url(javascript:alert(\'Injected\'))"&gt;
        &lt;script&gt;alert(\'Injected!\');&lt;/script&gt;
        '''
        self.assertEqual(response.data['story'], escaped_story)

    def test_safe_story(self):
        story = '''
            <p>test</p>
            <blockquote>test</blockquote>
            <pre>test</pre>
            <h1>test</h1>
            <h2>test</h2>
            <h3>test</h3>
            <h5>test</h5>
            <b>test</b>
            <strong>test</strong>
            <i>test</i>
            <ul><li><i>test</i></li></ul>
            <ol><li><i>test</i></li></ol>
            <a href="http://test.com" target="_blank">Test</a>
            <br>
        '''
        project = ProjectFactory.create(title="testproject",
                                        slug="testproject",
                                        story=story,
                                        owner=self.some_user,
                                        status=ProjectPhase.objects.get(
                                            slug='campaign'))

        response = self.client.get(reverse('project_detail',
                                           args=[project.slug]))
        self.assertEqual(response.data['story'], story)


class ProjectWallpostApiIntegrationTest(BluebottleTestCase):
    """
    Integration tests for the Project Media Wallpost API.
    """

    def setUp(self):
        super(ProjectWallpostApiIntegrationTest, self).setUp()

        self.init_projects()
        self.some_project = ProjectFactory.create(slug='someproject')
        self.another_project = ProjectFactory.create(slug='anotherproject')

        self.some_user = BlueBottleUserFactory.create()
        self.some_user_token = "JWT {0}".format(self.some_user.get_jwt_token())

        self.another_user = BlueBottleUserFactory.create()
        self.another_user_token = "JWT {0}".format(
            self.another_user.get_jwt_token())

        self.some_photo = './bluebottle/projects/test_images/loading.gif'
        self.another_photo = './bluebottle/projects/test_images/upload.png'

        self.media_wallposts_url = reverse('media_wallpost_list')
        self.media_wallpost_photos_url = reverse('mediawallpost_photo_list')

        self.text_wallposts_url = reverse('text_wallpost_list')
        self.wallposts_url = reverse('wallpost_list')

    def test_project_media_wallpost_crud(self):
        """
        Tests for creating, retrieving, updating and deleting a Project
        Media Wallpost.
        """
        self.owner_token = "JWT {0}".format(
            self.some_project.owner.get_jwt_token())

        # Create a Project Media Wallpost by Project Owner
        # Note: This test will fail when we require at least a video and/or a
        # text but that's what we want.
        wallpost_text = u'This is my super project!'
        response = self.client.post(self.media_wallposts_url,
                                    {'text': wallpost_text,
                                     'parent_type': 'project',
                                     'parent_id': self.some_project.slug},
                                    token=self.owner_token)
        self.assertEqual(response.status_code,
                         status.HTTP_201_CREATED,
                         response.data)
        self.assertEqual(response.data['text'],
                         u"<p>{0}</p>".format(wallpost_text))
        self.assertEqual(response.data['type'], u"media")

        # Retrieve the created Project Media Wallpost.
        project_wallpost_detail_url = "{0}{1}".format(self.media_wallposts_url,
                                                      str(response.data['id']))
        response = self.client.get(project_wallpost_detail_url,
                                   token=self.owner_token)

        self.assertEqual(response.status_code,
                         status.HTTP_200_OK,
                         response.data)
        self.assertEqual(response.data['text'],
                         u"<p>{0}</p>".format(wallpost_text))

        # Update the created Project Media Wallpost by author.
        new_wallpost_text = u'This is my super-duper project!'
        response = self.client.put(project_wallpost_detail_url,
                                   {'text': new_wallpost_text,
                                    'parent_type': 'project',
                                    'parent_id': self.some_project.slug},
                                   token=self.owner_token)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK,
                         response.data)
        self.assertEqual(response.data['text'],
                         u'<p>{0}</p>'.format(new_wallpost_text))

        # Delete Project Media Wallpost by author
        response = self.client.delete(
            project_wallpost_detail_url, token=self.owner_token)
        self.assertEqual(
            response.status_code, status.HTTP_204_NO_CONTENT, response)

        # Check that creating a Wallpost with project slug that doesn't exist
        # reports an error.
        response = self.client.post(self.media_wallposts_url,
                                    {'text': wallpost_text,
                                     'parent_type': 'project',
                                     'parent_id': 'allyourbasearebelongtous'},
                                    token=self.owner_token)
        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST, response.data)

        # Create Project Media Wallpost and retrieve by another user
        response = self.client.post(self.media_wallposts_url,
                                    {'text': wallpost_text,
                                     'parent_type': 'project',
                                     'parent_id': self.some_project.slug},
                                    token=self.owner_token)
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data)

        project_wallpost_detail_url = "{0}{1}".format(
            self.wallposts_url, str(response.data['id']))

        response = self.client.get(
            project_wallpost_detail_url, token=self.some_user_token)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK,
                         response.data)
        self.assertEqual(response.data['type'], u'media')
        self.assertEqual(response.data['text'],
                         u"<p>{0}</p>".format(wallpost_text))

        # Update Project Media Wallpost by someone else than Project Owner
        # should fail
        second_wallpost_text = "My project rocks!"
        response = self.client.post(self.media_wallposts_url,
                                    {'text': second_wallpost_text,
                                     'parent_type': 'project',
                                     'parent_id': self.some_project.slug},
                                    token=self.owner_token)
        self.assertEqual(response.status_code,
                         status.HTTP_201_CREATED,
                         response.data)

        response = self.client.put(project_wallpost_detail_url,
                                   {'text': new_wallpost_text, 'parent_type':
                                       'project',
                                    'parent_id': self.some_project.slug},
                                   token=self.some_user_token)
        self.assertEqual(
            response.status_code, status.HTTP_403_FORBIDDEN, response.data)

        # Deleting a Project Media Wallpost by non-author user should fail - by
        # some user
        response = self.client.delete(
            project_wallpost_detail_url, token=self.some_user_token)
        self.assertEqual(
            response.status_code, status.HTTP_403_FORBIDDEN, response)

        # Retrieve a list of the two Project Media Wallposts that we've just
        # added should work
        response = self.client.get(self.wallposts_url,
                                   {'parent_type': 'project',
                                    'parent_id': self.some_project.slug},
                                   token=self.some_user_token)
        self.assertEqual(
            response.status_code, status.HTTP_200_OK, response.data)

        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(
            response.data['results'][0]['text'],
            "<p>{0}</p>".format(second_wallpost_text))
        self.assertEqual(
            response.data['results'][1]['text'],
            "<p>{0}</p>".format(wallpost_text))

    def test_project_media_wallpost_photo(self):
        """
        Test connecting photos to wallposts
        """
        self.owner_token = "JWT {0}".format(
            self.some_project.owner.get_jwt_token())

        # Typically the photos are uploaded before the wallpost is uploaded so
        # we simulate that here
        photo_file = open(self.some_photo, mode='rb')
        response = self.client.post(self.media_wallpost_photos_url,
                                    {'photo': photo_file},
                                    token=self.owner_token, format='multipart')
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data)
        some_photo_detail_url = "{0}{1}".format(
            self.media_wallpost_photos_url, response.data['id'])

        # Create a Project Media Wallpost by Project Owner
        wallpost_text = 'Here are some pics!'
        response = self.client.post(self.media_wallposts_url,
                                    {'text': wallpost_text,
                                     'parent_type': 'project',
                                     'parent_id': self.some_project.slug},
                                    token=self.owner_token)
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(
            response.data['text'], "<p>{0}</p>".format(wallpost_text))
        some_wallpost_id = response.data['id']
        some_wallpost_detail_url = "{0}{1}".format(
            self.wallposts_url, some_wallpost_id)

        # Try to connect the photo to this new wallpost
        response = self.client.put(some_photo_detail_url,
                                   {'mediawallpost': some_wallpost_id},
                                   token=self.owner_token)
        self.assertEqual(
            response.status_code, status.HTTP_200_OK, response.data)

        # check that the wallpost now has 1 photo
        response = self.client.get(
            some_wallpost_detail_url, token=self.owner_token)
        self.assertEqual(len(response.data['photos']), 1)

        # Let's upload another photo
        photo_file = open(self.another_photo, mode='rb')
        response = self.client.post(self.media_wallpost_photos_url,
                                    {'photo': photo_file},
                                    token=self.owner_token, format='multipart')
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data)
        another_photo_detail_url = "{0}{1}".format(
            self.media_wallpost_photos_url, response.data['id'])

        # Create a wallpost by another user
        wallpost_text = 'Muy project is waaaaaay better!'
        response = self.client.post(self.media_wallposts_url,
                                    {'text': wallpost_text,
                                     'parent_type': 'project',
                                     'parent_id': self.another_project.slug,
                                     'email_followers': False},
                                    token=self.another_user_token)
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(
            response.data['text'], "<p>{0}</p>".format(wallpost_text))
        another_wallpost_id = response.data['id']

        # The other shouldn't be able to use the photo of the first user
        response = self.client.put(another_photo_detail_url,
                                   {'mediawallpost': another_wallpost_id},
                                   token=self.another_user_token)
        self.assertEqual(
            response.status_code, status.HTTP_403_FORBIDDEN, response.data)

        response = self.client.put(another_photo_detail_url,
                                   {'mediawallpost': some_wallpost_id},
                                   token=self.another_user_token)
        self.assertEqual(
            response.status_code, status.HTTP_403_FORBIDDEN, response.data)

        # Make sure the first user can't connect it's picture to someone else's
        # wallpost
        response = self.client.put(another_photo_detail_url,
                                   {'mediawallpost': another_wallpost_id},
                                   token=self.some_user_token)
        self.assertEqual(
            response.status_code, status.HTTP_403_FORBIDDEN, response.data)

        #  Create a text wallpost.
        text = "You have something nice going on here."
        response = self.client.post(self.text_wallposts_url,
                                    {'text': text,
                                     'parent_type': 'project',
                                     'parent_id': self.another_project.slug,
                                     'email_followers': False},
                                    token=self.owner_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED,
                         response.data)

        # Adding a photo to that should be denied.
        response = self.client.put(another_photo_detail_url,
                                   {'mediawallpost': another_wallpost_id},
                                   token=self.owner_token)
        self.assertEqual(
            response.status_code, status.HTTP_403_FORBIDDEN, response.data)

        # Add that second photo to our first wallpost and verify that will now
        # contain two photos.
        response = self.client.put(another_photo_detail_url,
                                   {'mediawallpost': some_wallpost_id},
                                   token=self.owner_token)
        self.assertEqual(
            response.status_code, status.HTTP_200_OK, response.data)

        response = self.client.get(
            some_wallpost_detail_url, token=self.owner_token)
        self.assertEqual(len(response.data['photos']), 2)

    def test_project_text_wallpost_crud(self):
        """
        Tests for creating, retrieving, updating and deleting text wallposts.
        """

        # Create text wallpost as not logged in guest should be denied
        text1 = 'Great job!'
        response = self.client.post(self.text_wallposts_url, {
            'text': text1, 'parent_type': 'project',
            'parent_id': self.some_project.slug})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Create TextWallpost as a logged in member should be allowed
        response = self.client.post(self.text_wallposts_url,
                                    {'text': text1,
                                     'parent_type': 'project',
                                     'parent_id': self.some_project.slug,
                                     'email_followers': False},
                                    token=self.some_user_token)
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertTrue(text1 in response.data['text'])

        # Retrieve text wallpost through Wallposts api
        wallpost_detail_url = "{0}{1}".format(
            self.wallposts_url, str(response.data['id']))
        response = self.client.get(
            wallpost_detail_url, token=self.some_user_token)
        self.assertEqual(
            response.status_code, status.HTTP_200_OK, response.data)
        self.assertTrue(text1 in response.data['text'])

        # Retrieve text wallpost through TextWallposts api
        wallpost_detail_url = "{0}{1}".format(
            self.wallposts_url, str(response.data['id']))
        response = self.client.get(
            wallpost_detail_url, token=self.some_user_token)
        self.assertEqual(
            response.status_code, status.HTTP_200_OK, response.data)
        self.assertTrue(text1 in response.data['text'])

        # Retrieve text wallpost through projectwallposts api by another user
        wallpost_detail_url = "{0}{1}".format(
            self.wallposts_url, str(response.data['id']))
        response = self.client.get(
            wallpost_detail_url, token=self.another_user_token)
        self.assertEqual(
            response.status_code, status.HTTP_200_OK, response.data)
        self.assertTrue(text1 in response.data['text'])

        # Create TextWallpost without a text should return an error
        response = self.client.post(self.text_wallposts_url,
                                    {'text': '', 'parent_type': 'project',
                                     'parent_id': self.some_project.slug},
                                    token=self.another_user_token)
        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertIsNotNone(response.data['text'])

        text2 = u'I liek this project!'

        # Create TextWallpost as another logged in member should be allowed
        response = self.client.post(self.text_wallposts_url,
                                    {'text': text2,
                                     'parent_type': 'project',
                                     'parent_id': self.some_project.slug,
                                     'email_followers': False},
                                    token=self.another_user_token)
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertTrue(text2 in response.data['text'])

        # Update TextWallpost by author is allowed
        text2a = u'I like this project!'
        wallpost_detail_url = "{0}{1}".format(self.text_wallposts_url,
                                              str(response.data['id']))
        response = self.client.put(wallpost_detail_url,
                                   {'text': text2a, 'parent_type': 'project',
                                    'parent_id': self.some_project.slug},
                                   token=self.another_user_token)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK,
                         response.data)
        self.assertEqual(u'<p>{0}</p>'.format(text2a), response.data['text'])

        # Update TextWallpost by another user (not the author) is not allowed
        text2b = u'Mess this up!'
        wallpost_detail_url = "{0}{1}".format(
            self.wallposts_url, str(response.data['id']))
        response = self.client.put(wallpost_detail_url,
                                   {'text': text2b,
                                    'project': self.some_project.slug},
                                   token=self.some_user_token)
        self.assertEqual(response.status_code,
                         status.HTTP_403_FORBIDDEN,
                         response.data)

    def test_projectwallpost_list(self):
        """
        Tests for list and (soft)deleting wallposts
        """

        # Create a bunch of Project Text Wallposts
        for char in 'abcdefghijklmnopqrstuv':
            text = char * 15
            response = self.client.post(self.text_wallposts_url,
                                        {'text': text,
                                         'parent_type': 'project',
                                         'parent_id': self.some_project.slug,
                                         'email_followers': False},
                                        token=self.some_user_token)

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # And a bunch of Project Media Wallposts
        self.owner_token = "JWT {0}".format(
            self.some_project.owner.get_jwt_token())
        for char in 'wxyz':
            text = char * 15
            response = self.client.post(self.media_wallposts_url,
                                        {'text': text, 'parent_type': 'project',
                                         'parent_id': self.some_project.slug},
                                        token=self.owner_token)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Retrieve a list of the 26 Project Wallposts
        # View Project Wallpost list works for author
        response = self.client.get(self.wallposts_url,
                                   {'parent_type': 'project',
                                    'parent_id': self.some_project.slug},
                                   token=self.owner_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)
        self.assertEqual(response.data['count'], 26)
        mediawallpost = response.data['results'][0]

        # Check that we're correctly getting a list with mixed types.
        self.assertEqual(mediawallpost['type'], 'media')

        # Delete a Media Wallpost and check that we can't retrieve it anymore
        project_wallpost_detail_url = "{0}{1}".format(
            self.wallposts_url, mediawallpost['id'])
        response = self.client.delete(
            project_wallpost_detail_url, token=self.owner_token)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        response = self.client.get(project_wallpost_detail_url,
                                   token=self.owner_token)
        self.assertEqual(response.status_code,
                         status.HTTP_404_NOT_FOUND,
                         response.data)

        # Wallpost List count should have decreased after deleting one
        response = self.client.get(self.wallposts_url,
                                   {'parent_type': 'project',
                                    'parent_id': self.some_project.slug},
                                   token=self.owner_token)
        self.assertEqual(response.data['count'], 25)

        # View Project Wallpost list works for guests.
        response = self.client.get(self.wallposts_url, {
            'parent_type': 'project',
            'parent_id': self.some_project.slug})
        self.assertEqual(
            response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(len(response.data['results']), 10)
        self.assertEqual(response.data['count'], 25)

        # Test filtering wallposts by different projects works.
        self.another_token = "JWT {0}".format(
            self.another_project.owner.get_jwt_token())

        for char in 'ABCD':
            text = char * 15
            response = self.client.post(self.media_wallposts_url,
                                        {'text': text, 'parent_type': 'project',
                                         'parent_id': self.another_project.slug},
                                        token=self.another_token)

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.get(
            self.wallposts_url, {'parent_type': 'project',
                                 'parent_id': self.some_project.slug})
        self.assertEqual(
            response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['count'], 25)

        response = self.client.get(self.wallposts_url,
                                   {'parent_type': 'project',
                                    'parent_id': self.another_project.slug},
                                   token=self.owner_token)
        self.assertEqual(
            response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['count'], 4)


class ChangeProjectStatuses(ProjectEndpointTestCase):
    def set_date_submitted(self, project):
        # Set a date_submitted value for the project
        yesterday = timezone.now() - timedelta(days=1)
        project.date_submitted = yesterday
        project.save()
        self.assertEquals(project.date_submitted, yesterday)

    def test_change_status_to_submitted(self):
        """
        Changing project status to submitted sets the date_submitted field
        """
        random_id = Project.objects.last().id - randint(0, Project.objects.count() - 1)
        project = Project.objects.get(id=random_id)
        self.assertTrue(project.date_submitted is None)

        # Change status of project to Needs work
        project.status = ProjectPhase.objects.get(slug="plan-submitted")
        project.save()

        loaded_project = Project.objects.get(pk=project.pk)
        self.assertTrue(loaded_project.date_submitted is not None)

    def test_change_status_to_campaign(self):
        """
        Changing project status to campaign sets the campaign_started field
        """
        project = ProjectFactory.create(title="testproject",
                                        slug="testproject",
                                        status=ProjectPhase.objects.get(slug='plan-new'))
        self.assertTrue(project.date_submitted is None)
        self.assertTrue(project.campaign_started is None)

        project.status = ProjectPhase.objects.get(slug="campaign")
        project.save()

        loaded_project = Project.objects.get(pk=project.pk)
        self.assertTrue(loaded_project.campaign_started is not None)

    def test_change_status_to_need_to_work(self):
        """
        Changing status to needs work clears the date_submitted field of a
        project
        """
        project = Project.objects.order_by('?').all()[0]
        self.set_date_submitted(project)

        # Change status of project to Needs work
        project.status = ProjectPhase.objects.get(slug="plan-needs-work")
        project.save()

        loaded_project = Project.objects.get(pk=project.pk)
        self.assertEquals(loaded_project.date_submitted, None)

    def test_change_status_to_new(self):
        """
        Changing status to new clears the date_submitted field of a project
        """
        project = Project.objects.get(
            id=Project.objects.last().id - randint(0,
                                                   Project.objects.count() - 1))
        self.set_date_submitted(project)

        # Change status of project to Needs work
        project.status = ProjectPhase.objects.get(slug="plan-new")
        project.save()

        self.assertEquals(project.date_submitted, None)

    def test_campaign_project_got_funded_no_overfunding(self):
        """
        A project gets a donation and gets funded. The project does not allow
        overfunding so the status changes,
        the campaign funded field is populated and campaign_ended field is
        populated
        """
        organization = OrganizationFactory.create()
        project = ProjectFactory.create(title="testproject",
                                        slug="testproject",
                                        organization=organization,
                                        status=ProjectPhase.objects.get(
                                            slug="campaign"),
                                        amount_asked=100,
                                        allow_overfunding=False)

        self.assertTrue(project.campaign_ended is None)
        self.assertTrue(project.campaign_funded is None)

        DonationFactory.create(project=project, amount=10000)

        Project.objects.get(pk=project.pk)

    def test_campaign_project_got_funded_allow_overfunding(self):
        """
        A project gets funded and allows overfunding. The project status does
        not change, the campaign_funded field
        is populated but the campaign_ended field is not populated
        """
        project = ProjectFactory.create(title="testproject",
                                        slug="testproject",
                                        status=ProjectPhase.objects.get(
                                            slug="campaign"),
                                        amount_asked=100)

        self.assertTrue(project.campaign_ended is None)
        self.assertTrue(project.campaign_funded is None)

        DonationFactory.create(project=project, amount=10000)

        loaded_project = Project.objects.get(pk=project.pk)
        self.assertTrue(loaded_project.campaign_ended is None)

        self.assertEquals(loaded_project.status,
                          ProjectPhase.objects.get(slug="campaign"))

    def test_campaign_project_not_funded(self):
        """
        A donation is made but the project is not funded. The status doesn't
        change and neither the campaign_ended
        or campaign_funded are populated.
        """
        project = ProjectFactory.create(title="testproject",
                                        slug="testproject",
                                        status=ProjectPhase.objects.get(
                                            slug="campaign"),
                                        amount_asked=100)

        self.assertTrue(project.campaign_ended is None)
        self.assertTrue(project.campaign_funded is None)

        DonationFactory.create(project=project, amount=99)

        loaded_project = Project.objects.get(pk=project.pk)
        self.assertTrue(loaded_project.campaign_ended is None)
        # FIXME: Re-enable this if donations are ok again
        # self.assertTrue(loaded_project.campaign_funded is None)
        self.assertEquals(
            loaded_project.status, ProjectPhase.objects.get(slug="campaign"))

    def test_project_expired_under_20_euros(self):
        """
        The deadline of a project expires but its not funded. The status
        changes, the campaign_ended field is populated
        with the deadline, the campaign_funded field is empty.
        Under 20 euros the status becomes 'closed'.
        """
        organization = OrganizationFactory.create()
        project = ProjectFactory.create(title="testproject",
                                        slug="testproject",
                                        organization=organization,
                                        status=ProjectPhase.objects.get(
                                            slug="campaign"),
                                        amount_asked=100)

        self.assertTrue(project.campaign_ended is None)
        self.assertTrue(project.campaign_funded is None)

        project.deadline = timezone.now() - timedelta(days=10)
        project.save()

        loaded_project = Project.objects.get(pk=project.pk)
        self.assertTrue(loaded_project.campaign_ended)
        self.assertTrue(loaded_project.campaign_funded is None)
        self.assertEquals(
            loaded_project.status, ProjectPhase.objects.get(slug="closed"))

    def test_project_expired_more_than_20_euros(self):
        """
        The deadline of a project expires but its not funded. The status
        changes, the campaign_ended field is populated with the deadline,
        the campaign_funded field is empty.
        Above 20 euros the status becomes 'done-incomplete'.
        """

        now = timezone.now()

        organization = OrganizationFactory.create()
        project = ProjectFactory.create(title="testproject",
                                        slug="testproject",
                                        organization=organization,
                                        campaign_started=now - timezone.
                                        timedelta(days=15),
                                        status=ProjectPhase.objects.
                                        get(slug="campaign"),
                                        amount_asked=100)

        order = OrderFactory.create()

        donation = DonationFactory.create(
            project=project,
            order=order,
            amount=60
        )
        donation.save()

        order.locked()
        order.save()
        order.success()
        order.save()

        project.deadline = timezone.now() - timedelta(days=10)
        project.save()

        # project.save()
        self.assertTrue(project.campaign_ended is not None)
        self.assertTrue(project.campaign_funded is None)

        loaded_project = Project.objects.get(pk=project.pk)
        self.assertTrue(loaded_project.campaign_ended)
        self.assertTrue(loaded_project.campaign_funded is None)
        self.assertEquals(loaded_project.status,
                          ProjectPhase.objects.get(slug="done-incomplete"))


class ProjectMediaApi(BluebottleTestCase):
    """
    Test that project media return media (pictures & videos) from wallposts.
    """

    def setUp(self):
        super(ProjectMediaApi, self).setUp()
        self.init_projects()

        self.some_user = BlueBottleUserFactory.create()
        self.another_user = BlueBottleUserFactory.create()
        self.some_user_token = "JWT {0}".format(self.some_user.get_jwt_token())
        self.another_user_token = "JWT {0}".format(self.another_user.get_jwt_token())
        self.project = ProjectFactory.create(owner=self.some_user)

        mwp1 = MediaWallpostFactory.create(content_object=self.project,
                                           video_url='https://youtu.be/Bal2U5jxZDQ')
        MediaWallpostPhotoFactory.create(mediawallpost=mwp1)
        MediaWallpostPhotoFactory.create(mediawallpost=mwp1)
        MediaWallpostPhotoFactory.create(mediawallpost=mwp1)
        MediaWallpostPhotoFactory.create(mediawallpost=mwp1)
        MediaWallpostPhotoFactory.create(mediawallpost=mwp1)

        mwp2 = MediaWallpostFactory.create(content_object=self.project,
                                           video_url='https://youtu.be/Bal2U5jxZDQ')
        MediaWallpostPhotoFactory.create(mediawallpost=mwp2)
        MediaWallpostPhotoFactory.create(mediawallpost=mwp2)
        MediaWallpostPhotoFactory.create(mediawallpost=mwp2)

        self.project_media_url = reverse('project-media-detail',
                                         kwargs={'slug': self.project.slug})

    def test_project_media_pictures(self):
        response = self.client.get(self.project_media_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

        self.assertEqual(len(response.data['pictures']), 8)
        self.assertEqual(len(response.data['videos']), 2)

    def test_project_hide_media_picture(self):
        # Hide a picture from results media
        response = self.client.get(self.project_media_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(len(response.data['pictures']), 8)

        pic_id = response.data['pictures'][0]['id']
        pic_data = {
            'id': pic_id,
            'results_page': False
        }

        # Only project owner can hide an image
        picture_url = reverse('project-media-photo-detail', kwargs={'pk': pic_id})
        response = self.client.put(picture_url, pic_data, token=self.another_user_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.put(picture_url, pic_data, token=self.some_user_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check the image is not listed anymore
        response = self.client.get(self.project_media_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(len(response.data['pictures']), 7)


class ProjectSupportersApi(ProjectEndpointTestCase):
    """
    Check that project supports api return lists with donors, wallposters and task members.
    """

    def setUp(self):
        self.init_projects()
        self.project = ProjectFactory.create()
        self.user1 = BlueBottleUserFactory.create()
        self.user2 = BlueBottleUserFactory.create()
        self.user3 = BlueBottleUserFactory.create()
        self.user4 = BlueBottleUserFactory.create()

        DonationFactory.create(project=self.project,
                               order=OrderFactory(status='success', user=self.user1))
        DonationFactory.create(project=self.project,
                               order=OrderFactory(status='success', user=self.user1))
        DonationFactory.create(project=self.project,
                               order=OrderFactory(status='success', user=self.user1))
        DonationFactory.create(project=self.project,
                               order=OrderFactory(status='pending', user=self.user2))
        DonationFactory.create(project=self.project,
                               order=OrderFactory(status='success', user=self.user3))
        DonationFactory.create(project=self.project, anonymous=True,
                               order=OrderFactory(status='success', user=self.user4))
        DonationFactory.create(project=self.project,
                               order=OrderFactory(status='success', user=None))

        TextWallpostFactory.create(content_object=self.project, author=self.user1)
        TextWallpostFactory.create(content_object=self.project, author=self.user1)
        TextWallpostFactory.create(content_object=self.project, author=self.user2)
        TextWallpostFactory.create(content_object=self.project, author=self.user3)

        task = TaskFactory(project=self.project)

        TaskMemberFactory.create(member=self.user1, task=task, status='accepted')
        TaskMemberFactory.create(member=self.user2, task=task, status='applied')
        TaskMemberFactory.create(member=self.user3, task=task, status='realized')

        self.project_supporters_url = reverse('project-supporters-detail',
                                              kwargs={'slug': self.project.slug})

    def test_project_media_pictures(self):

        response = self.client.get(self.project_supporters_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

        self.assertEqual(len(response.data['donors']), 3)
        self.assertEqual(len(response.data['posters']), 3)
        self.assertEqual(len(response.data['task_members']), 2)

    def test_project_media_pictures_only_from_project(self):
        self.task = TaskFactory.create()
        TextWallpostFactory.create(content_object=self.task, author=self.user4)

        response = self.client.get(self.project_supporters_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

        self.assertEqual(len(response.data['donors']), 3)
        self.assertEqual(len(response.data['posters']), 3)
        self.assertEqual(len(response.data['task_members']), 2)


class ProjectVotesTest(BluebottleTestCase):
    """
    Integration tests for the Project Media Wallpost API.
    """

    def setUp(self):
        super(ProjectVotesTest, self).setUp()

        self.init_projects()

        phase = ProjectPhase.objects.get(slug='voting')
        self.some_project = ProjectFactory.create(slug='someproject', status=phase)
        self.another_project = ProjectFactory.create(slug='anotherproject', status=phase)

        self.some_user = BlueBottleUserFactory.create()
        self.another_user = BlueBottleUserFactory.create()

        self.some_user_token = "JWT {0}".format(self.some_user.get_jwt_token())

        self.project_url = reverse('project_detail', args=[self.some_project.slug])

    def test_has_voted_anonymous(self):
        """
        Tests for creating, retrieving, updating and deleting a Project
        Media Wallpost.
        """
        response = self.client.get(self.project_url)
        self.assertFalse(response.data['has_voted'])

    def test_has_not_voted(self):
        """
        Tests for creating, retrieving, updating and deleting a Project
        Media Wallpost.
        """
        response = self.client.get(self.project_url, token=self.some_user_token)
        self.assertFalse(response.data['has_voted'])

    def test_has_voted(self):
        """
        Tests for creating, retrieving, updating and deleting a Project
        Media Wallpost.
        """
        VoteFactory.create(project=self.some_project, voter=self.some_user)
        response = self.client.get(self.project_url, token=self.some_user_token)
        self.assertTrue(response.data['has_voted'])

    def test_has_voted_another_project(self):
        """
        Tests for creating, retrieving, updating and deleting a Project
        Media Wallpost.
        """
        VoteFactory.create(project=self.another_project, voter=self.some_user)
        response = self.client.get(self.project_url, token=self.some_user_token)
        self.assertFalse(response.data['has_voted'])

    def test_has_voted_another_user(self):
        """
        Tests for creating, retrieving, updating and deleting a Project
        Media Wallpost.
        """
        VoteFactory.create(project=self.some_project, voter=self.another_user)
        response = self.client.get(self.project_url, token=self.some_user_token)

        self.assertFalse(response.data['has_voted'])

    def test_has_voted_within_category(self):
        """
        Tests for creating, retrieving, updating and deleting a Project
        Media Wallpost.
        """
        category = CategoryFactory.create()

        self.some_project.categories = [category]
        self.another_project.categories = [category]

        self.some_project.save()
        self.another_project.save()

        VoteFactory.create(project=self.another_project, voter=self.some_user)
        response = self.client.get(self.project_url, token=self.some_user_token)

        self.assertTrue(response.data['has_voted'])

    def test_has_voted_within_category_expired_project(self):
        """
        Tests for creating, retrieving, updating and deleting a Project
        Media Wallpost.
        """
        category = CategoryFactory.create()

        self.some_project.categories = [category]
        self.another_project.categories = [category]
        self.another_project.status = ProjectPhase.objects.get(slug='voting-done')

        self.some_project.save()
        self.another_project.save()

        VoteFactory.create(project=self.another_project, voter=self.some_user)
        response = self.client.get(self.project_url, token=self.some_user_token)

        self.assertFalse(response.data['has_voted'])

    def test_another_user_has_voted_within_category(self):
        """
        Tests for creating, retrieving, updating and deleting a Project
        Media Wallpost.
        """
        category = CategoryFactory.create()

        self.some_project.categories = [category]
        self.another_project.categories = [category]

        self.some_project.save()
        self.another_project.save()

        VoteFactory.create(project=self.another_project, voter=self.another_user)
        response = self.client.get(self.project_url, token=self.some_user_token)

        self.assertFalse(response.data['has_voted'])


@override_settings(PAYMENT_METHODS=[{
    'provider': 'docdata',
    'id': 'docdata-ideal',
    'profile': 'ideal',
    'name': 'iDEAL',
    'restricted_countries': ('NL', ),
    'supports_recurring': False,
    'currencies': {
        'EUR': {'min_amount': 5, 'max_amount': 100},
        'USD': {'min_amount': 5, 'max_amount': 100},
        'NGN': {'min_amount': 5, 'max_amount': 100},
        'XOF': {'min_amount': 5, 'max_amount': 100},
    }
}])
class ProjectCurrenciesApiTest(BluebottleTestCase):
    """
    Integration tests currencies in the Project API.
    """

    def setUp(self):
        super(ProjectCurrenciesApiTest, self).setUp()

        self.some_user = BlueBottleUserFactory.create()
        self.some_user_token = "JWT {0}".format(self.some_user.get_jwt_token())

        self.another_user = BlueBottleUserFactory.create()
        self.another_user_token = "JWT {0}".format(
            self.another_user.get_jwt_token())

        self.init_projects()

        self.some_project = ProjectFactory.create(currencies=['EUR'])
        self.another_project = ProjectFactory.create(currencies=['NGN', 'USD'])

    def test_project_currencies(self):
        self.project_url = reverse('project_detail', args=[self.some_project.slug])
        response = self.client.get(self.project_url)
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.data['currencies'], ['EUR'])

        self.project_url = reverse('project_detail', args=[self.another_project.slug])
        response = self.client.get(self.project_url)
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertListEqual(response.data['currencies'], [u'NGN', u'USD'])
