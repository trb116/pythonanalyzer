import autocomplete_light
from django.conf.urls import patterns, url

from extension_test import views

autocomplete_light.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^about/(?P<template>.+)/?$', views.DynamicTemplateView.as_view(), name="about"),
)
