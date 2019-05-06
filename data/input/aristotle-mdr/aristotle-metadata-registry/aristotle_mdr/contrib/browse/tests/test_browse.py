from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase, override_settings, modify_settings
from django.test.utils import setup_test_environment
from django.utils import timezone

import aristotle_mdr.models as models
import aristotle_mdr.perms as perms
from aristotle_mdr.utils import url_slugify_concept
from aristotle_mdr.forms.creation_wizards import WorkgroupVerificationMixin,CheckIfModifiedMixin

setup_test_environment()
from aristotle_mdr.tests import utils
import datetime


class LoggedInViewConceptBrowsePages(utils.LoggedInViewPages):
    defaults = {}
    
    def setUp(self):
        super(LoggedInViewConceptBrowsePages, self).setUp()

        self.item1 = self.itemType.objects.create(name="Test Item 1 (visible to tested viewers)",definition=" ",workgroup=self.wg1,**self.defaults)
        self.item2 = self.itemType.objects.create(name="Test Item 2 (NOT visible to tested viewers)",definition=" ",workgroup=self.wg2,**self.defaults)
        self.item3 = self.itemType.objects.create(name="Test Item 3 (visible to tested viewers)",definition=" ",workgroup=self.wg1,**self.defaults)
        self.item4 = self.itemType.objects.create(name="Test Item 3 (visible to tested viewers)",definition=" ",workgroup=self.wg1,
            readyToReview=True,**self.defaults)
        self.ra.register(self.item4,self.ra.public_state,self.su)

    def test_anon_can_view_browse(self):
        self.logout()
        response = self.client.get(
            reverse("browse_concepts",args=[self.itemType._meta.app_label,self.itemType._meta.model_name])
            )
        self.assertEqual(response.status_code,200)
        self.assertTrue(self.item4.name in response.content)
        self.assertTrue(self.item2.name not in response.content)

    def test_editor_can_view_browse(self):
        self.login_editor()
        response = self.client.get(
            reverse("browse_concepts",args=[self.itemType._meta.app_label,self.itemType._meta.model_name])
            )
        self.assertEqual(response.status_code,200)
        self.assertTrue(self.item1.name in response.content)
        self.assertTrue(self.item4.name in response.content)
        self.assertTrue(self.item2.name not in response.content)

class ObjectClassViewPage(LoggedInViewConceptBrowsePages,TestCase):
    url_name='objectClass'
    itemType=models.ObjectClass
class PropertyViewPage(LoggedInViewConceptBrowsePages,TestCase):
    url_name='property'
    itemType=models.Property
class UnitOfMeasureViewPage(LoggedInViewConceptBrowsePages,TestCase):
    url_name='unitOfMeasure'
    itemType=models.UnitOfMeasure
class ValueDomainViewPage(LoggedInViewConceptBrowsePages,TestCase):
    url_name='valueDomain'
    itemType=models.ValueDomain

class ConceptualDomainViewPage(LoggedInViewConceptBrowsePages,TestCase):
    url_name='conceptualDomain'
    itemType=models.ConceptualDomain
class DataElementConceptViewPage(LoggedInViewConceptBrowsePages,TestCase):
    url_name='dataElementConcept'
    itemType=models.DataElementConcept
class DataElementViewPage(LoggedInViewConceptBrowsePages,TestCase):
    url_name='dataElement'
    itemType=models.DataElement
class DataElementDerivationViewPage(LoggedInViewConceptBrowsePages,TestCase):
    url_name='dataelementderivation'
    itemType=models.DataElementDerivation
