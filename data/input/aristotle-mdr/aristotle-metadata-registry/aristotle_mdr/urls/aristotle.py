import autocomplete_light

from django.conf.urls import patterns, url
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView

from haystack.query import SearchQuerySet
from haystack.views import search_view_factory

import aristotle_mdr.views as views
import aristotle_mdr.forms as forms

autocomplete_light.autodiscover()
sqs = SearchQuerySet()

urlpatterns = patterns(
    'aristotle_mdr.views',

    url(r'^/?$', TemplateView.as_view(template_name='aristotle_mdr/static/home.html'), name="home"),

    # all the below take on the same form:
    # url(r'^itemType/(?P<iid>\d+)?/?
    # Allowing for a blank ItemId (iid) allows aristotle to redirect to /about/itemtype instead of 404ing
    url(r'^valuedomain/(?P<iid>\d+)?/edit/values/(?P<value_type>permissible|supplementary)/?$', views.editors.valuedomain_value_edit, name='valueDomain_edit_values'),

    url(r'^workgroup/(?P<iid>\d+)(?:-(?P<name_slug>[A-Za-z0-9\-]+))?/?$', views.workgroups.workgroup, name='workgroup'),
    url(r'^workgroup/(?P<iid>\d+)/members/?$', views.workgroups.members, name='workgroupMembers'),
    url(r'^workgroup/(?P<iid>\d+)/items/?$', views.workgroups.items, name='workgroupItems'),
    url(r'^workgroup/addMembers/(?P<iid>\d+)$', views.workgroups.add_members, name='addWorkgroupMembers'),
    url(r'^workgroup/(?P<iid>\d+)/archive/?$', views.workgroups.archive, name='archive_workgroup'),
    url(r'^remove/WorkgroupRole/(?P<iid>\d+)/(?P<role>[A-Za-z\-]+)/(?P<userid>\d+)/?$', views.workgroups.remove_role, name='removeWorkgroupRole'),

    url(r'^discussions/?$', views.discussions.all, name='discussions'),
    url(r'^discussions/new/?$', views.discussions.new, name='discussionsNew'),
    url(r'^discussions/workgroup/(?P<wgid>\d+)/?$', views.discussions.workgroup, name='discussionsWorkgroup'),
    url(r'^discussions/post/(?P<pid>\d+)/?$', views.discussions.post, name='discussionsPost'),
    url(r'^discussions/post/(?P<pid>\d+)/newcomment/?$', views.discussions.new_comment, name='discussionsPostNewComment'),
    url(r'^discussions/delete/comment/(?P<cid>\d+)/?$', views.discussions.delete_comment, name='discussionsDeleteComment'),
    url(r'^discussions/delete/post/(?P<pid>\d+)/?$', views.discussions.delete_post, name='discussionsDeletePost'),
    url(r'^discussions/edit/comment/(?P<cid>\d+)/?$', views.discussions.edit_comment, name='discussionsEditComment'),
    url(r'^discussions/edit/post/(?P<pid>\d+)/?$', views.discussions.edit_post, name='discussionsEditPost'),
    url(r'^discussions/post/(?P<pid>\d+)/toggle/?$', views.discussions.toggle_post, name='discussionsPostToggle'),

    # url(r'^item/(?P<iid>\d+)/?$', views.items.concept, name='item'),
    url(r'^item/(?P<iid>\d+)/edit/?$', views.editors.EditItemView.as_view(), name='edit_item'),
    url(r'^item/(?P<iid>\d+)/clone/?$', views.editors.CloneItemView.as_view(), name='clone_item'),
    url(r'^item/(?P<iid>\d+)/history/?$', views.ConceptHistoryCompareView.as_view(), name='item_history'),
    url(r'^item/(?P<iid>\d+)/registrationHistory/?$', views.registrationHistory, name='registrationHistory'),

    url(r'^item/(?P<iid>\d+)(?:\/(?P<model_slug>\w+)\/(?P<name_slug>.+))?/?$', views.concept, name='item'),
    url(r'^item/(?P<iid>\d+)(?:\/.*)?$', views.concept, name='item'),  # Catch every other 'item' URL and throw it for a redirect

    url(r'^unmanaged/measure/(?P<iid>\d+)(?:\/(?P<model_slug>\w+)\/(?P<name_slug>.+))?/?$', views.measure, name='measure'),

    # url(r'^create/?$', views.item, name='item'),
    url(r'^create/?$', views.create_list, name='createList'),
    url(r'^create/(aristotle_mdr/)?dataelementconcept$', views.wizards.DataElementConceptWizard.as_view(), name='createDataElementConcept'),
    url(r'^create/(aristotle_mdr/)?dataelement$', views.wizards.DataElementWizard.as_view(), name='createDataElement'),
    url(r'^create/(?P<app_label>.+)/(?P<model_name>.+)/?$', views.wizards.create_item, name='createItem'),
    url(r'^create/(?P<model_name>.+)/?$', views.wizards.create_item, name='createItem'),

    url(r'^download/(?P<downloadType>[a-zA-Z0-9\-\.]+)/(?P<iid>\d+)/?$', views.download, name='download'),

    url(r'^action/supersede/(?P<iid>\d+)$', views.supersede, name='supersede'),
    url(r'^action/deprecate/(?P<iid>\d+)$', views.deprecate, name='deprecate'),
    url(r'^action/bulkaction/?$', views.bulk_actions.bulk_action, name='bulk_action'),
    url(r'^action/r2r/(?P<iid>\d+)?$', views.mark_ready_to_review, name='mark_ready_to_review'),
    url(r'^action/compare/?$', views.comparator.compare_concepts, name='compare_concepts'),

    url(r'^changestatus/(?P<iid>\d+)$', views.changeStatus, name='changeStatus'),
    # url(r'^remove/WorkgroupUser/(?P<iid>\d+)/(?P<userid>\d+)$', views.removeWorkgroupUser, name='removeWorkgroupUser'),

    url(r'^account/?$', RedirectView.as_view(url='account/home/', permanent=True)),
    url(r'^account/home/?$', views.user_pages.home, name='userHome'),
    url(r'^account/roles/?$', views.user_pages.roles, name='userRoles'),
    url(r'^account/admin/?$', views.user_pages.admin_tools, name='userAdminTools'),
    url(r'^account/admin/statistics/?$', views.user_pages.admin_stats, name='userAdminStats'),
    url(r'^account/edit/?$', views.user_pages.edit, name='userEdit'),
    url(r'^account/recent/?$', views.user_pages.recent, name='userRecentItems'),
    url(r'^account/favourites/?$', views.user_pages.favourites, name='userFavourites'),
    url(r'^account/workgroups/?$', views.user_pages.workgroups, name='userWorkgroups'),
    url(r'^account/workgroups/archives/?$', views.user_pages.workgroup_archives, name='user_workgroups_archives'),
    url(r'^account/notifications(?:/folder/(?P<folder>all))?/?$', views.user_pages.inbox, name='userInbox'),

    url(r'^account/registrartools/?$', views.user_pages.registrar_tools, name='userRegistrarTools'),
    url(r'^account/registrartools/readyforreview/?$', views.user_pages.review_list, name='userReadyForReview'),

    url(r'^registrationauthority/(?P<iid>\d+)?(?:\/(?P<name_slug>.+))?/?$', views.registrationauthority, name='registrationAuthority'),
    url(r'^registrationauthorities/?$', views.allRegistrationAuthorities, name='allRegistrationAuthorities'),
    url(r'^account/toggleFavourite/(?P<iid>\d+)/?$', views.toggleFavourite, name='toggleFavourite'),

    url(r'^extensions/?$', views.extensions, name='extensions'),

    url(r'^about/aristotle/?$', TemplateView.as_view(template_name='aristotle_mdr/static/aristotle_mdr.html'), name="aboutMain"),
    url(r'^about/(?P<template>.+)/?$', views.DynamicTemplateView.as_view(), name="about"),

    url(r'^accessibility/?$', TemplateView.as_view(template_name='aristotle_mdr/static/accessibility.html'), name="accessibility"),

    url(
        r'^search/?',
        search_view_factory(
            view_class=views.PermissionSearchView,
            template='search/search.html',
            searchqueryset=None,
            form_class=forms.search.PermissionSearchForm
            ),
        name='search'
    ),
)
