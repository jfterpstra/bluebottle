from bluebottle.test.utils import BluebottleTestCase
from bluebottle.utils.model_dispatcher import get_task_model, get_project_model
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.tasks import TaskFactory, TaskMemberFactory

from bluebottle.bb_projects.models import ProjectPhase

BB_TASK_MODEL = get_task_model()
BB_PROJECT_MODEL = get_project_model()

