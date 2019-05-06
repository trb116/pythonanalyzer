from django.test import TestCase
from django.core.urlresolvers import reverse
from django.utils import timezone
import aristotle_mdr.models as models
import aristotle_mdr.perms as perms
import aristotle_mdr.tests.utils as utils

import datetime

from django.test.utils import setup_test_environment
setup_test_environment()

"""
This test suite houses tests to third-party modules to ensure they are being run how
we need them.
"""

class AristotleAutocompletes(utils.LoggedInViewPages, TestCase):
    def setUp(self):
        super(AristotleAutocompletes, self).setUp()

        # There would be too many tests to test every item type against every other
        # But they all have identical logic, so one test should suffice
        self.item1 = models.ObjectClass.objects.create(name="AC1", workgroup=self.wg1)
        self.item2 = models.ObjectClass.objects.create(name="AC2", workgroup=self.wg1)
        self.item3 = models.ObjectClass.objects.create(name="AC3", workgroup=self.wg2)
        self.item4 = models.Property.objects.create(name="AC4", workgroup=self.wg1)

    def test_concept_autocompletes(self):
        self.login_editor()

        # We aren't going to run the full gambit here
        # Just enough to prove that
        #  a. _concept autocomplete can return more than one item typr
        #  b. specialised autcompleted *only* return their own item type
        #  c. autocompletes don't return items invisible to users

        response = self.client.get(
            '/autocomplete/Autocomplete_concept/',
            {
                'q': 'AC',
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue('AC1' in response.content)
        self.assertTrue('AC2' in response.content)
        self.assertTrue('AC3' not in response.content)
        self.assertTrue('AC4' in response.content)
        
        response = self.client.get(
            '/autocomplete/AutocompleteObjectClass/',
            {
                'q': 'AC',
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue('AC1' in response.content)
        self.assertTrue('AC2' in response.content)
        self.assertTrue('AC3' not in response.content)
        self.assertTrue('AC4' not in response.content)
        
        self.item1.readyToReview = True
        self.item1.save()
        registered = self.ra.register(self.item1,models.STATES.standard,self.registrar,
            registrationDate=timezone.now()+datetime.timedelta(days=-1)
        )
        self.assertTrue(models.ObjectClass.objects.get(name='AC1').is_public())

        self.logout()
        response = self.client.get(
            '/autocomplete/AutocompleteObjectClass/',
            {
                'q': 'AC',
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue('AC1' in response.content)
        self.assertTrue('AC2' not in response.content)
        self.assertTrue('AC3' not in response.content)
        self.assertTrue('AC4' not in response.content)

    def test_concept_autocomplete_statuses(self):
        # see also
        # tests.main.test_search.test_current_statuses_only_in_search_results_and_index
        
        from django.contrib.auth.models import User
        self.registrar = User.objects.create_user('stryker','william.styker@weaponx.mil','mutantsMustDie')
        self.ra.giveRoleToUser('registrar',self.registrar)

        self.logout()
        response = self.client.post(reverse('friendly_login'),
                    {'username': 'stryker', 'password': 'mutantsMustDie'})

        self.assertEqual(response.status_code,302) # logged in
        self.assertTrue(perms.user_is_registrar(self.registrar,self.ra))

        dp = models.ObjectClass.objects.create(name="deadpool",
                definition="not really an xman, no matter how much he tries",
                workgroup=self.wg1,readyToReview=True)
        dp = models.ObjectClass.objects.get(pk=dp.pk) # Un-cache
        self.assertTrue(perms.user_can_view(self.registrar,dp))
        self.assertFalse(dp.is_public())

        self.ra.register(dp,models.STATES.incomplete,self.registrar,
            registrationDate=timezone.now()+datetime.timedelta(days=-7)
        )

        self.ra.register(dp,models.STATES.standard,self.registrar,
            registrationDate=timezone.now()+datetime.timedelta(days=-1)
        )

        response = self.client.get(
            '/autocomplete/AutocompleteObjectClass/',
            {
                'q': 'deadpoo',
            }
        )

        self.assertTrue('standard' in response.content.lower())
        self.assertTrue('incomplete' not in response.content.lower())
