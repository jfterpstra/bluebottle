from django.conf.urls import patterns, url
from ..views import SuggestionList, SuggestionDetail

urlpatterns = patterns(
    '',
    url(r'^$', SuggestionList.as_view(), name='suggestion_list'),
    url(r'^(?P<pk>\d+)$', SuggestionDetail.as_view(),
        name='suggestion_detail')
)