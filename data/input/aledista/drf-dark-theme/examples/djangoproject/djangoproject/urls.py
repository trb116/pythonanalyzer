from django.conf.urls import patterns, url

from .views import TestApiView


urlpatterns = patterns('',
   url(r'^$', TestApiView.as_view(), name='api_test'),
)
