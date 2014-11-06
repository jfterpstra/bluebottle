from ..views import MobileIndexView
from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url('^$', MobileIndexView.as_view(), name='mobile-index'),
)