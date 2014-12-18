from serializers import LatestDonationSerializer
from bluebottle.donations.models import Donation
from bluebottle.utils.utils import StatusDefinition
from rest_framework import permissions, generics
from bluebottle.utils.model_dispatcher import get_project_model
import logging
from django.template import RequestContext, Context, loader
from django.http import HttpResponseServerError

from django.views.generic import TemplateView


PROJECT_MODEL = get_project_model()

logger = logging.getLogger(__name__)

# For showing the latest donations
class LatestDonationsList(generics.ListAPIView):
    model = Donation
    serializer_class = LatestDonationSerializer
    permission_classes = (permissions.IsAdminUser,)
    paginate_by = 20

    def get_queryset(self):
        qs = super(LatestDonationsList, self).get_queryset()
        qs = qs.order_by('-created')
        return qs.filter(order__status__in=[StatusDefinition.PENDING, StatusDefinition.SUCCESS])




def handler500(request, template_name='500.html'):
    """
    500 error handler which tries to use a RequestContext - unless an error
    is raised, in which a normal Context is used with just the request
    available.

    Templates: `500.html`
    Context: None
    """

    # Try returning using a RequestContext
    try:
        context = RequestContext(request)
    except:
        logger.warn('Error getting RequestContext for ServerError page.')
        context = Context({'request': request})

    t = loader.get_template('500.html')  # You need to create a 500.html template.
    return HttpResponseServerError(t.render(context))


class HomeView(TemplateView):
    """
    Home view for the site.
    """

    template_name = 'base.html'

    def get_context_data(self, **kwargs):
        """ Add some extra context. """
        context = {}

        return context
