from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.utils import LanguageFactory
from django.utils.text import slugify
from onepercentclub.tests.factory_models.project_factories import OnePercentProjectFactory
from onepercentclub.tests.utils import OnePercentTestCase


class HomepageTestCase(OnePercentTestCase):
    """ Test that the homepage doesn't error out if no/a campaign is available """

    def setUp(self):
        self.init_projects()

        # Create and activate user.
        self.user = BlueBottleUserFactory.create(email='johndoe@example.com', primary_language='en')
        title = u'Mobile payments for everyone 2!'
        language = LanguageFactory.create(code='en')

        self.project = OnePercentProjectFactory.create(title=title, slug=slugify(title), amount_asked=100000, owner=self.user)
        self.project.status = ProjectPhase.objects.get(slug='campaign')
        self.project.is_campaign = True
        self.project.money_donated = 0
        self.project.language = language
        self.project.save()

        self.homepage_url = '/api/homepage/en'
