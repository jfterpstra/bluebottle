import json
import re

from django.core import mail
from bluebottle.test.utils import BluebottleTestCase

from rest_framework import status

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory


class UserApiIntegrationTest(BluebottleTestCase):
    """
    Integration tests for the User API.
    """
    def setUp(self):
        super(UserApiIntegrationTest, self).setUp()

        self.user_1 = BlueBottleUserFactory.create()
        self.user_1_token = "JWT {0}".format(self.user_1.get_jwt_token())

        self.user_2 = BlueBottleUserFactory.create()
        self.user_2_token = "JWT {0}".format(self.user_2.get_jwt_token())

        self.current_user_api_url = '/api/users/current'
        self.user_create_api_url = '/api/users/'
        self.user_profile_api_url = '/api/users/profiles/'
        self.user_settings_api_url = '/api/users/settings/'
        self.user_activation_api_url = '/api/users/activate/'
        self.user_password_reset_api_url = '/api/users/passwordreset'
        self.user_password_set_api_url = '/api/users/passwordset/'

    def test_user_profile_retrieve_and_update(self):
        """
        Test retrieving a public user profile by id.
        """
        user_profile_url = "{0}{1}".format(self.user_profile_api_url, self.user_1.id)
        response = self.client.get(user_profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.user_1.id)

        # Profile should not be able to be updated by anonymous users.
        full_name = {'first_name': 'Nijntje', 'last_name': 'het Konijntje'}
        response = self.client.put(user_profile_url, full_name)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)

        # Profile should be able to be updated by logged in user.
        response = self.client.put(user_profile_url, full_name, token=self.user_1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['first_name'], full_name.get('first_name'))
        self.assertEqual(response.data['last_name'], full_name.get('last_name'))

        self.client.logout()

    def test_unauthenticated_user(self):
        """
        Test retrieving the currently logged in user while not logged in.
        """
        # Test unauthenticated user doesn't return 500 error.
        response = self.client.get(self.current_user_api_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.data)

    def test_current_user(self):
        """
        Test retrieving the currently logged in user after login.
        """
        response = self.client.get(self.current_user_api_url, token=self.user_1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['first_name'], self.user_1.first_name)

        self.client.logout()

    def test_user_settings(self):
        """
        Test retrieving and updating a user's settings by id.
        """
        # Settings shouldn't be accessible until a user is logged in.
        user_settings_url = "{0}{1}".format(self.user_settings_api_url, self.user_1.id)
        response = self.client.get(user_settings_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, response.data)

        # Settings should be accessible after a user is logged in.
        user_1_settings_url = "{0}{1}".format(self.user_settings_api_url, self.user_1.id)
        response = self.client.get(user_1_settings_url, token=self.user_1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['email'], self.user_1.email)
        self.assertFalse(response.data['newsletter'])

        # Test that the settings can be updated.
        response = self.client.put(user_1_settings_url, {'newsletter': True}, token=self.user_1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertTrue(response.data['newsletter'])

        self.client.logout()

    def test_user_create(self):
        """
        Test creating a user with the api, activating the new user and
        updating the settings once logged in.
        """
        # Create a user.
        new_user_email = 'nijntje27@hetkonijntje.nl'
        new_user_password = 'testing'
        response = self.client.post(self.user_create_api_url, {'email': new_user_email,
                                                               'password': new_user_password})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        token = "JWT {0}".format(response.data['jwt_token'])
        user_id = response.data['id']

        # Test that the settings can be updated.
        new_user_settings_url = "{0}{1}".format(self.user_settings_api_url, user_id)
        response = self.client.put(new_user_settings_url, {'newsletter': True}, token=token)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertTrue(response.data['newsletter'])

        # Test that the email field is required on user create.
        response = self.client.post(self.user_create_api_url, {'password': new_user_password})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertEqual(response.data['email'][0], 'This field is required.')

    def test_generate_username(self):
        new_user1_email = 'nijntje74@hetkonijntje.nl'
        new_user2_email = 'nijntje89@hetkonijntje.nl'
        new_user3_email = 'nijntje21@hetkonijntje.nl'
        new_user4_email = 'nijntje45@hetkonijntje.nl'
        first_name = 'Nijntje'
        last_name = 'het Konijntje'
        new_user_password = 'password'

        # Test username generation with duplicates.
        response = self.client.post(self.user_create_api_url, {'first_name': first_name,
                                                               'last_name': last_name,
                                                               'email': new_user1_email,
                                                               'password': new_user_password})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data['username'], 'nijntjehetkonijntje')

        response = self.client.post(self.user_create_api_url, {'first_name': first_name,
                                                               'last_name': last_name,
                                                               'email': new_user2_email,
                                                               'password': new_user_password})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data['username'], 'nijntjehetkonijntje_2')

        response = self.client.post(self.user_create_api_url, {'first_name': first_name,
                                                               'last_name': last_name,
                                                               'email': new_user3_email,
                                                               'password': new_user_password})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data['username'], 'nijntjehetkonijntje_3')

        # Test username generation with no first name or lastname.
        response = self.client.post(self.user_create_api_url, {'email': new_user4_email,
                                                               'password': new_user_password})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data['username'], 'nijntje45')

    def test_password_reset(self):
        # Setup: create a user.
        new_user_email = 'nijntje94@hetkonijntje.nl'
        new_user_password = 'password'
        response = self.client.post(self.user_create_api_url, {'email': new_user_email,
                                                               'password': new_user_password})
        token = "JWT {0}".format(response.data['jwt_token'])
        user_id = response.data['id']

        # Test: resetting the password should be allowed.
        response = self.client.put(self.user_password_reset_api_url, {'email': new_user_email})
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(len(mail.outbox), 1)

        # Setup: get the password reset token and url.
        c = re.compile('\/(?P<uidb36>[0-9A-Za-z]{1,13})-(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})\/', re.DOTALL)
        m = c.search(mail.outbox[0].body)
        password_set_url = '{0}{1}-{2}'.format(self.user_password_set_api_url, m.group(1), m.group(2))

        # Test: check that non-matching passwords produce a validation error.
        passwords = {'new_password1': 'rabbit', 'new_password2': 'rabbitt'}
        response = self.client.put(password_set_url, passwords)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        self.assertEqual(response.data['new_password2'][0], "The two password fields didn't match.")

        # Test: check that updating the password works when the passwords match.
        passwords['new_password2'] = 'rabbit'
        response = self.client.put(password_set_url, passwords)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

        # Test: check that the user can login with the new password.
        new_user_settings_url = "{0}{1}".format(self.user_settings_api_url, user_id)
        response = self.client.get(new_user_settings_url, token=token)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['email'], new_user_email)

        # Test: check that trying to reuse the password reset link doesn't work.
        response = self.client.put(password_set_url, passwords)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.data)


class LocaleMiddlewareTest(BluebottleTestCase):
    """
    Integration tests for the User API.
    """
    def setUp(self):
        super(LocaleMiddlewareTest, self).setUp()

        self.user_1 = BlueBottleUserFactory.create()
        self.user_1.primary_language = 'en'
        self.user_1.save()

        self.user_1_token = "JWT {0}".format(self.user_1.get_jwt_token())

    def test_early_redirect_to_user_language(self):
        response = self.client.get('/nl/', follow=False, token=self.user_1_token)
        self.assertRedirects(response, '/en/')

    def test_no_redirect_for_non_language_urls(self):
        response = self.client.get('/api/', follow=False, token=self.user_1_token)
        self.assertTrue(response.status_code, 200)

        response = self.client.get('/', follow=False, token=self.user_1_token)
        self.assertTrue(response.status_code, 200)

    def test_no_redirect_for_anonymous_user(self):
        response = self.client.get('/nl/', follow=False)
        self.assertTrue(response.status_code, 200)


class UserProfileUpdateTests(BluebottleTestCase):
    """
    Integration tests for the User API with dependencies on different bluebottle apps.
    """
    def setUp(self):
        super(UserProfileUpdateTests, self).setUp()

        self.user_1 = BlueBottleUserFactory.create()
        self.user_2 = BlueBottleUserFactory.create()
        self.current_user_api_url = '/api/users/current'
        self.user_create_api_url = '/api/users/'
        self.user_profile_api_url = '/api/users/profiles/'
        self.user_settings_api_url = '/api/users/settings/'
        self.user_activation_api_url = '/api/users/activate/'
        self.user_password_reset_api_url = '/api/users/passwordreset'
        self.user_password_set_api_url = '/api/users/passwordset/'

