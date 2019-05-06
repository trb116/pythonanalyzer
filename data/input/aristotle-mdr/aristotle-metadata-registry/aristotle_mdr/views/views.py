from django.apps import apps
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.exceptions import PermissionDenied, ImproperlyConfigured
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.db import transaction
from django.forms.models import modelformset_factory
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.template import RequestContext, TemplateDoesNotExist
from django.template.defaultfilters import slugify
from django.template.loader import select_template
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView
from django.utils import timezone
from django.utils.decorators import method_decorator
import datetime

import reversion
from reversion.revisions import default_revision_manager
from reversion_compare.views import HistoryCompareDetailView

from aristotle_mdr.perms import user_can_view, user_can_edit, user_can_change_status
from aristotle_mdr import perms
from aristotle_mdr.utils import cache_per_item_user, concept_to_dict, construct_change_message, url_slugify_concept
from aristotle_mdr import forms as MDRForms
from aristotle_mdr import models as MDR
from aristotle_mdr.utils import concept_to_clone_dict, get_concepts_for_apps
from aristotle_mdr import exceptions as registry_exceptions

from haystack.views import SearchView, FacetedSearchView

import logging

logger = logging.getLogger(__name__)
logger.debug("Logging started for " + __name__)

PAGES_PER_RELATED_ITEM = 15


class DynamicTemplateView(TemplateView):
    def get_template_names(self):
        return ['aristotle_mdr/static/%s.html' % self.kwargs['template']]


class ConceptHistoryCompareView(HistoryCompareDetailView):
    model = MDR._concept
    pk_url_kwarg = 'iid'
    template_name = "aristotle_mdr/actions/concept_history_compare.html"

    def get_object(self, queryset=None):
        item = super(ConceptHistoryCompareView, self).get_object(queryset)
        if not user_can_view(self.request.user, item):
            raise PermissionDenied
        self.model = item.item.__class__  # Get the subclassed object
        return item

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ConceptHistoryCompareView, self).dispatch(*args, **kwargs)


class HelpTemplateView(TemplateView):
    def get_template_names(self):
        return ['aristotle_mdr/static/help/%s.html' % self.kwargs['template']]


def get_if_user_can_view(objtype, user, iid):
    item = get_object_or_404(objtype, pk=iid)
    if user_can_view(user, item):
        return item
    else:
        return False


def render_if_user_can_view(item_type, request, *args, **kwargs):
    # request = kwargs.pop('request')
    return render_if_condition_met(request, user_can_view, item_type, *args, **kwargs)


@login_required
def render_if_user_can_edit(item_type, request, *args, **kwargs):
    request = kwargs.pop('request')
    return render_if_condition_met(request, user_can_edit, item_type, *args, **kwargs)


def download(request, downloadType, iid=None):
    """
    By default, ``aristotle_mdr.views.download`` is called whenever a URL matches
    the pattern defined in ``aristotle_mdr.urls_aristotle``::

        download/(?P<downloadType>[a-zA-Z0-9\-\.]+)/(?P<iid>\d+)/?

    This is passed into ``download`` which resolves the item id (``iid``), and
    determins if a user has permission to view the request item with that id. If
    a user is allowed to download this file, ``download`` iterates through each
    download type defined in ``ARISTOTLE_DOWNLOADS``.

    A download option tuple takes the following form form::

        ('file_type','display_name','font_awesome_icon_name','module_name'),

    With ``file_type`` allowing only ASCII alphanumeric and underscores,
    ``display_name`` can be any valid python string,
    ``font_awesome_icon_name`` can be any Font Awesome icon and
    ``module_name`` is the name of the python module that provides a downloader
    for this file type.

    For example, included with Aristotle-MDR is a PDF downloader which has the
    download definition tuple::

            ('pdf','PDF','fa-file-pdf-o','aristotle_mdr'),

    Where a ``file_type`` multiple is defined multiple times, **the last matching
    instance in the tuple is used**.

    Next, the module that is defined for a ``file_type`` is dynamically imported using
    ``exec``, and is wrapped in a ``try: except`` block to catch any exceptions. If
    the ``module_name`` does not match the regex ``^[a-zA-Z0-9\_]+$`` ``download``
    raises an exception.

    If the module is able to be imported, ``downloader.py`` from the given module
    is imported, this file **MUST** have a ``download`` function defined which returns
    a Django ``HttpResponse`` object of some form.
    """
    item = MDR._concept.objects.get_subclass(pk=iid)
    item = get_if_user_can_view(item.__class__, request.user, iid)
    if not item:
        if request.user.is_anonymous():
            return redirect(reverse('friendly_login') + '?next=%s' % request.path)
        else:
            raise PermissionDenied

    downloadOpts = getattr(settings, 'ARISTOTLE_DOWNLOADS', "")
    module_name = ""
    for d in downloadOpts:
        dt = d[0]
        if dt == downloadType:
            module_name = d[3]
    if module_name:
        import re
        if not re.search('^[a-zA-Z0-9\-\.]+$', downloadType):  # pragma: no cover
            # Invalid downloadType
            raise registry_exceptions.BadDownloadTypeAbbreviation("Download type can only be composed of letters, numbers, hyphens or periods.")
        elif not re.search('^[a-zA-Z0-9\_]+$', module_name):  # pragma: no cover
            # bad module_name
            raise registry_exceptions.BadDownloadModuleName("Download name isn't a valid Python module name.")
        try:
            downloader = None
            # dangerous - we are really trusting the settings creators here.
            exec("import %s.downloader as downloader" % module_name)
            return downloader.download(request, downloadType, item)
        except TemplateDoesNotExist:
            raise Http404

    raise Http404


def concept(*args, **kwargs):
    return render_if_user_can_view(MDR._concept, *args, **kwargs)


def measure(request, iid, model_slug, name_slug):
    item = get_object_or_404(MDR.Measure, pk=iid).item
    template = select_template([item.template])
    context = RequestContext(
        request,
        {
            'item': item,
            # 'view': request.GET.get('view', '').lower(),
            # 'last_edit': last_edit
        }
    )

    return HttpResponse(template.render(context))

    # return render_if_user_can_view(MDR.Measure, *args, **kwargs)


@cache_per_item_user(ttl=300, cache_post=False)
def render_if_condition_met(request, condition, objtype, iid, model_slug=None, name_slug=None, subpage=None):
    item = get_object_or_404(objtype, pk=iid).item
    if item._meta.model_name != model_slug or not slugify(item.name).startswith(str(name_slug)):
        return redirect(url_slugify_concept(item))
    if not condition(request.user, item):
        if request.user.is_anonymous():
            return redirect(reverse('friendly_login') + '?next=%s' % request.path)
        else:
            raise PermissionDenied

    # We add a user_can_edit flag in addition to others as we have odd rules around who can edit objects.
    isFavourite = request.user.is_authenticated() and request.user.profile.is_favourite(item)

    last_edit = default_revision_manager.get_for_object_reference(
        item.__class__,
        item.pk,
    ).first()

    default_template = "%s/concepts/%s.html" % (item.__class__._meta.app_label, item.__class__._meta.model_name)
    template = select_template([default_template, item.template])
    context = RequestContext(
        request,
        {
            'item': item,
            # 'view': request.GET.get('view', '').lower(),
            'isFavourite': isFavourite,
            'last_edit': last_edit
        }
    )

    return HttpResponse(template.render(context))


def registrationHistory(request, iid):
    item = get_if_user_can_view(MDR._concept, request.user, iid)
    if not item:
        if request.user.is_anonymous():
            return redirect(reverse('friendly_login') + '?next=%s' % request.path)
        else:
            raise PermissionDenied

    history = item.statuses.order_by("registrationAuthority", "-registrationDate")
    out = {}
    for status in history:
        if status.registrationAuthority in out.keys():
            out[status.registrationAuthority].append(status)
        else:
            out[status.registrationAuthority] = [status]

    return render(request, "aristotle_mdr/registrationHistory.html", {'item': item, 'history': out})


def unauthorised(request, path=''):
    if request.user.is_anonymous():
        return render(request, "401.html", {"path": path, "anon": True, }, status=401)
    else:
        return render(request, "403.html", {"path": path, "anon": True, }, status=403)


def create_list(request):
    if request.user.is_anonymous():
        return redirect(reverse('friendly_login') + '?next=%s' % request.path)
    if not perms.user_is_editor(request.user):
        raise PermissionDenied

    aristotle_apps = getattr(settings, 'ARISTOTLE_SETTINGS', {}).get('CONTENT_EXTENSIONS', [])
    aristotle_apps += ["aristotle_mdr"]
    out = {}

    for m in get_concepts_for_apps(aristotle_apps):
        # Only output subclasses of 11179 concept
        app_models = out.get(m.app_label, {'app': None, 'models': []})
        if app_models['app'] is None:
            try:
                app_models['app'] = getattr(apps.get_app_config(m.app_label), 'verbose_name')
            except:
                app_models['app'] = "No name"  # Where no name is configured in the app_config, set a dummy so we don't keep trying
        app_models['models'].append((m, m.model_class()))
        out[m.app_label] = app_models

    return render(request, "aristotle_mdr/create/create_list.html", {'models': out})


@login_required
def toggleFavourite(request, iid):
    item = get_object_or_404(MDR._concept, pk=iid).item
    if not user_can_view(request.user, item):
        if request.user.is_anonymous():
            return redirect(reverse('friendly_login') + '?next=%s' % request.path)
        else:
            raise PermissionDenied
    request.user.profile.toggleFavourite(item)
    if request.GET.get('next', None):
        return redirect(request.GET.get('next'))
    if item.concept in request.user.profile.favourites.all():
        message = _("%s added to favourites.") % (item.name)
    else:
        message = _("%s removed from favourites.") % (item.name)
    message = _(message + " Review your favourites from the user menu.")
    messages.add_message(request, messages.SUCCESS, message)
    return redirect(url_slugify_concept(item))


def registrationauthority(request, iid, *args, **kwargs):
    objtype = MDR.RegistrationAuthority
    if iid is None:
        app_name = objtype._meta.app_label
        return redirect(reverse("%s:about" % app_name, args=["".join(objtype._meta.verbose_name.lower().split())]))
    item = get_object_or_404(objtype, pk=iid).item

    return render(request, item.template, {'item': item.item})


def allRegistrationAuthorities(request):
    ras = MDR.RegistrationAuthority.objects.order_by('name')
    return render(request, "aristotle_mdr/allRegistrationAuthorities.html", {'registrationAuthorities': ras})


# Actions


def mark_ready_to_review(request, iid):
    item = get_object_or_404(MDR._concept, pk=iid).item
    if not (item and user_can_edit(request.user, item)):
        if request.user.is_anonymous():
            return redirect(reverse('friendly_login') + '?next=%s' % request.path)
        else:
            raise PermissionDenied

    if request.method == 'POST':  # If the form has been submitted...
        if item.is_registered:
            raise PermissionDenied
        else:
            with transaction.atomic(), reversion.revisions.create_revision():
                reversion.revisions.set_user(request.user)
                item.readyToReview = not item.readyToReview
                item.save()
        return HttpResponseRedirect(url_slugify_concept(item))
    else:
        return render(request, "aristotle_mdr/actions/mark_ready_to_review.html", {"item": item})


def changeStatus(request, iid):
    item = get_object_or_404(MDR._concept, pk=iid).item
    if not (item and user_can_change_status(request.user, item)):
        if request.user.is_anonymous():
            return redirect(reverse('friendly_login') + '?next=%s' % request.path)
        else:
            raise PermissionDenied
    # There would be an else here, but both branches above return,
    # so we've chopped it out to prevent an arrow anti-pattern.
    if request.method == 'POST':  # If the form has been submitted...
        form = MDRForms.ChangeStatusForm(request.POST, user=request.user)  # A form bound to the POST data
        if form.is_valid():
            # process the data in form.cleaned_data as required
            ras = form.cleaned_data['registrationAuthorities']
            state = form.cleaned_data['state']
            regDate = form.cleaned_data['registrationDate']
            cascade = form.cleaned_data['cascadeRegistration']
            changeDetails = form.cleaned_data['changeDetails']
            with transaction.atomic(), reversion.revisions.create_revision():
                reversion.revisions.set_user(request.user)
                for ra in ras:
                    if cascade:
                        register_method = ra.cascaded_register
                    else:
                        register_method = ra.register

                    register_method(
                        item,
                        state,
                        request.user,
                        changeDetails=changeDetails,
                        registrationDate=regDate,
                    )
                    # TODO: notification and message on success/failure
            return HttpResponseRedirect(url_slugify_concept(item))
    else:
        form = MDRForms.ChangeStatusForm(user=request.user)
    matrix={}

    visibility = "hidden"
    if item._is_locked:
        visibility = "locked"
    if item._is_public:
        visibility = "public"

    from aristotle_mdr.models import WORKGROUP_OWNERSHIP, STATES
    import json

    for ra in request.user.profile.registrarAuthorities:
        if item.workgroup.ownership == WORKGROUP_OWNERSHIP.authority:
            owner = ra in item.workgroup.registrationAuthorities.all()
        elif item.workgroup.ownership == WORKGROUP_OWNERSHIP.registry:
            owner = True
        ra_matrix = {'name': ra.name, 'states': {}}
        for s, _ in STATES:
            if s > ra.public_state:
                ra_matrix['states'][s] = [visibility, "public"][owner]
            elif s > ra.locked_state:
                ra_matrix['states'][s] = [visibility, "locked"][owner]
            else:
                ra_matrix['states'][s] = [visibility, "hidden"][owner]
        matrix[ra.id] = ra_matrix

    return render(
        request,
        "aristotle_mdr/actions/changeStatus.html",
        {
            "item": item,
            "form": form,
            "status_matrix": json.dumps(matrix),
            "visibility": visibility
        }
    )


def supersede(request, iid):
    item = get_object_or_404(MDR._concept, pk=iid).item
    if not (item and user_can_edit(request.user, item)):
        if request.user.is_anonymous():
            return redirect(reverse('friendly_login') + '?next=%s' % request.path)
        else:
            raise PermissionDenied
    qs=item.__class__.objects.all()
    if request.method == 'POST':  # If the form has been submitted...
        form = MDRForms.SupersedeForm(request.POST, user=request.user, item=item, qs=qs)  # A form bound to the POST data
        if form.is_valid():
            with transaction.atomic(), reversion.revisions.create_revision():
                reversion.revisions.set_user(request.user)
                item.superseded_by = form.cleaned_data['newerItem']
                item.save()
            return HttpResponseRedirect(url_slugify_concept(item))
    else:
        form = MDRForms.SupersedeForm(item=item, user=request.user, qs=qs)
    return render(request, "aristotle_mdr/actions/supersedeItem.html", {"item": item, "form": form})


def deprecate(request, iid):
    item = get_object_or_404(MDR._concept, pk=iid).item
    if not (item and user_can_edit(request.user, item)):
        if request.user.is_anonymous():
            return redirect(reverse('friendly_login') + '?next=%s' % request.path)
        else:
            raise PermissionDenied
    qs=item.__class__.objects.filter().editable(request.user)
    if request.method == 'POST':  # If the form has been submitted...
        form = MDRForms.DeprecateForm(request.POST, user=request.user, item=item, qs=qs)  # A form bound to the POST data
        if form.is_valid():
            # Check use the itemset as there are permissions issues and we want to remove some:
            #  Everything that was superseded, but isn't in the returned set
            #  Everything that was in the returned set, but isn't already superseded
            #  Everything left over can stay the same, as its already superseded
            #    or wasn't superseded and is staying that way.
            with transaction.atomic(), reversion.revisions.create_revision():
                reversion.revisions.set_user(request.user)
                for i in item.supersedes.all():
                    if i not in form.cleaned_data['olderItems'] and user_can_edit(request.user, i):
                        item.supersedes.remove(i)
                for i in form.cleaned_data['olderItems']:
                    if user_can_edit(request.user, i):  # Would check item.supersedes but its a set
                        item.supersedes.add(i)
            return HttpResponseRedirect(url_slugify_concept(item))
    else:
        form = MDRForms.DeprecateForm(user=request.user, item=item, qs=qs)
    return render(request, "aristotle_mdr/actions/deprecateItems.html", {"item": item, "form": form})


def valuedomain_value_edit(request, iid, value_type):
    item = get_object_or_404(MDR.ValueDomain, pk=iid).item
    if not user_can_edit(request.user, item):
        if request.user.is_anonymous():
            return redirect(reverse('friendly_login') + '?next=%s' % request.path)
        else:
            raise PermissionDenied
    value_model = {
        'permissible': MDR.PermissibleValue,
        'supplementary': MDR.SupplementaryValue
    }.get(value_type, None)
    if not value_model:
        raise Http404

    num_values = value_model.objects.filter(valueDomain=item.id).count()
    if num_values > 0:
        extra = 0
    else:
        extra = 1
    ValuesFormSet = modelformset_factory(
        value_model,
        can_delete=True,  # dont need can_order is we have an order field
        fields=('order', 'value', 'meaning'),
        extra=extra
        )
    if request.method == 'POST':
        formset = ValuesFormSet(request.POST, request.FILES)
        if formset.is_valid():
                with transaction.atomic(), reversion.revisions.create_revision():
                    item.save()  # do this to ensure we are saving reversion records for the value domain, not just the values
                    formset.save(commit=False)
                    for form in formset.forms:
                        if form['value'].value() == '' and form['meaning'].value() == '':
                            continue  # Skip over completely blank entries.
                        if form['id'].value() not in [deleted_record['id'].value() for deleted_record in formset.deleted_forms]:
                            value = form.save(commit=False)  # Don't immediately save, we need to attach the value domain
                            value.valueDomain = item
                            value.save()
                    for obj in formset.deleted_objects:
                        obj.delete()
                    # formset.save(commit=True)
                    reversion.revisions.set_user(request.user)
                    reversion.revisions.set_comment(construct_change_message(request, None, [formset]))

                return redirect(reverse("aristotle_mdr:item", args=[item.id]))
    else:
        formset = ValuesFormSet(
            queryset=value_model.objects.filter(valueDomain=item.id),
            initial=[{'order': num_values, 'value': '', 'meaning': ''}]
            )
    return render(
        request,
        "aristotle_mdr/actions/edit_value_domain_values.html",
        {'item': item, 'formset': formset, 'value_type': value_type, 'value_model': value_model}
    )


def extensions(request):
    content=[]
    aristotle_apps = getattr(settings, 'ARISTOTLE_SETTINGS', {}).get('CONTENT_EXTENSIONS', [])

    if aristotle_apps:
        for app_label in aristotle_apps:
            app=apps.get_app_config(app_label)
            try:
                app.about_url = reverse('%s:about' % app_label)
            except:
                pass  # if there is no about URL, thats ok.
            content.append(app)

    content = list(set(content))
    aristotle_downloads = getattr(settings, 'ARISTOTLE_DOWNLOADS', [])
    downloads=dict()
    if aristotle_downloads:
        for download in aristotle_downloads:
            app_label = download[3]
            app_details = downloads.get(
                app_label,
                {'app': apps.get_app_config(app_label), 'downloads': []}
            )
            try:
                app_details['about_url'] = reverse('%s:about' % app_label)
            except:
                pass  # if there is no about URL, thats ok.
            app_details['downloads'].append(download)
            downloads[app_label]=app_details

    return render(
        request,
        "aristotle_mdr/static/extensions.html",
        {'content_extensions': content, 'download_extensions': downloads, }
    )


# Search views

class PermissionSearchView(FacetedSearchView):
    def build_form(self):
        form = super(self.__class__, self).build_form()
        form.request = self.request
        return form
