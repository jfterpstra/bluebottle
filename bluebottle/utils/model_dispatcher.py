from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.db.models import get_model


def get_task_skill_model():
    return get_model_class('TASKS_SKILL_MODEL')


def get_task_model():
    return get_model_class('TASKS_TASK_MODEL')


def get_taskmember_model():
    return get_model_class('TASKS_TASKMEMBER_MODEL')


def get_taskfile_model():
    return get_model_class('TASKS_TASKFILE_MODEL')


def get_project_model():
    return get_model_class('PROJECTS_PROJECT_MODEL')


def get_donation_model():
    return get_model_class('DONATIONS_DONATION_MODEL')


def get_order_model():
    return get_model_class('ORDERS_ORDER_MODEL')


def get_fundraiser_model():
    return get_model_class('FUNDRAISERS_FUNDRAISER_MODEL')


def get_organization_model():
    return get_model_class('ORGANIZATIONS_ORGANIZATION_MODEL')


def get_organizationmember_model():
    return get_model_class('ORGANIZATIONS_MEMBER_MODEL')


def get_organizationdocument_model():
    return get_model_class('ORGANIZATIONS_DOCUMENT_MODEL')


def get_project_phaselog_model():
    return get_model_class('PROJECTS_PHASELOG_MODEL')


def get_auth_user_model():
    return get_user_model()


def get_model_class(model_name=None):
    """
    Returns a model class
    model_name: The model eg 'User' or 'Project'
    """

    #remove this
    if model_name == 'AUTH_USER_MODEL':
        model = get_user_model()

    else:
        model_path = getattr(settings, model_name)
        try:
            app_label, model_class_name = model_path.split('.')
        except ValueError:
            raise ImproperlyConfigured(
                "{0} must be of the form 'app_label.model_name'").format(model_name)

        model = get_model(app_label, model_class_name)
        # import ipdb; ipdb.set_trace()
        if model is None:
            raise ImproperlyConfigured(
                "{0} refers to model '{0}' that has not been "
                "installed".format(model_name))

    return model