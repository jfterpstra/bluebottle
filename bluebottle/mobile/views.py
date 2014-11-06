from django.views.generic import TemplateView


class MobileIndexView(TemplateView):
    template_name = "mobile/index.html"
