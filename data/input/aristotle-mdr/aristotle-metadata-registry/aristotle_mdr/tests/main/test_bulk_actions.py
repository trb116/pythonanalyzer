from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase, override_settings
import aristotle_mdr.models as models
import aristotle_mdr.perms as perms
import aristotle_mdr.tests.utils as utils

from django.test.utils import setup_test_environment
setup_test_environment()


class BulkWorkgroupActionsPage(utils.LoggedInViewPages, TestCase):
    def setUp(self):
        super(BulkWorkgroupActionsPage, self).setUp()

        # There would be too many tests to test every item type against every other
        # But they all have identical logic, so one test should suffice
        self.item1 = models.ObjectClass.objects.create(name="OC1", workgroup=self.wg1)
        self.item2 = models.ObjectClass.objects.create(name="OC2", workgroup=self.wg1)
        self.item3 = models.ObjectClass.objects.create(name="OC3", workgroup=self.wg1)
        self.item4 = models.Property.objects.create(name="Prop4", workgroup=self.wg2)

    def test_bulk_add_favourite_on_permitted_items(self):
        self.login_editor()

        self.assertEqual(self.editor.profile.favourites.count(), 0)
        response = self.client.post(
            reverse('aristotle:bulk_action'),
            {
                'bulkaction': 'add_favourites',
                'items': [self.item1.id, self.item2.id],
            }
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.editor.profile.favourites.count(), 2)

    def test_bulk_add_favourite_on_forbidden_items(self):
        self.login_editor()

        self.assertEqual(self.editor.profile.favourites.count(), 0)
        response = self.client.post(
            reverse('aristotle:bulk_action'),
            {
                'bulkaction': 'add_favourites',
                'items': [self.item1.id, self.item4.id],
            },
            follow=True
        )
        self.assertEqual(self.editor.profile.favourites.count(), 1)
        self.assertFalse(self.item4 in self.editor.profile.favourites.all())
        self.assertTrue("Some items failed, they had the id&#39;s: %s" % self.item4.id in response.content)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)

    def test_bulk_change_workgroup_for_superuser(self):
        self.new_workgroup = models.Workgroup.objects.create(name="new workgroup")
        self.new_workgroup.submitters.add(self.editor)
        self.login_superuser()
        
        response = self.client.post(
            reverse('aristotle:bulk_action'),
            {
                'bulkaction': 'move_workgroup',
                'items': [self.item1.id, self.item2.id],
                'workgroup': [self.new_workgroup.id],
                "confirmed": True
            }
        )

        self.assertTrue(self.item1.concept in self.new_workgroup.items.all())
        self.assertTrue(self.item2.concept in self.new_workgroup.items.all())

        self.logout()
        self.login_editor()

        response = self.client.post(
            reverse('aristotle:bulk_action'),
            {
                'bulkaction': 'move_workgroup',
                'items': [self.item1.id, self.item2.id],
                'workgroup': [self.wg1.id],
                "confirmed": True
            },
            follow=True
        )

        self.assertTrue(self.item1.concept in self.new_workgroup.items.all())
        self.assertTrue(self.item2.concept in self.new_workgroup.items.all())

        self.assertTrue("Forbbiden" in response.content)

    @override_settings(ARISTOTLE_SETTINGS=dict(settings.ARISTOTLE_SETTINGS, WORKGROUP_CHANGES=['submitter']))
    def test_bulk_change_workgroup_for_editor__for_some_items(self):
        self.new_workgroup = models.Workgroup.objects.create(name="new workgroup")
        self.new_workgroup.submitters.add(self.editor)
        self.login_editor()
        
        self.assertTrue(self.item1.concept not in self.new_workgroup.items.all())
        self.assertTrue(self.item2.concept not in self.new_workgroup.items.all())
        self.assertTrue(self.item4.concept not in self.new_workgroup.items.all())

        response = self.client.post(
            reverse('aristotle:bulk_action'),
            {
                'bulkaction': 'move_workgroup',
                'items': [self.item1.id, self.item2.id, self.item4.id],
                'workgroup': [self.new_workgroup.id],
                "confirmed": True
            },
            follow=True
        )

        self.assertTrue(self.item1.concept in self.new_workgroup.items.all())
        self.assertTrue(self.item2.concept in self.new_workgroup.items.all())
        self.assertTrue(self.item4.concept not in self.new_workgroup.items.all())

        self.assertTrue("Some items failed, they had the id&#39;s: %(bad_ids)s" % {
            'bad_ids': ",".join(map(str,[self.item4.pk]))
        } in response.content)

        self.logout()
        self.login_superuser()


        response = self.client.post(
            reverse('aristotle:bulk_action'),
            {
                'bulkaction': 'move_workgroup',
                'items': [self.item1.id, self.item2.id, self.item4.id],
                'workgroup': [self.wg1.id],
                "confirmed": True
            },
            follow=True
        )

        self.assertTrue(self.item1.concept in self.wg1.items.all())
        self.assertTrue(self.item2.concept in self.wg1.items.all())
        self.assertTrue(self.item4.concept in self.wg1.items.all())

        self.assertTrue("Some items failed, they had the id&#39;s" not in response.content)

    def test_bulk_remove_favourite(self):
        self.login_editor()

        self.assertEqual(self.editor.profile.favourites.count(), 0)
        response = self.client.post(
            reverse('aristotle:bulk_action'),
            {
                'bulkaction': 'add_favourites',
                'items': [self.item1.id, self.item2.id],
            }
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.editor.profile.favourites.count(), 2)

        response = self.client.post(
            reverse('aristotle:bulk_action'),
            {
                'bulkaction': 'remove_favourites',
                'items': [self.item1.id, self.item2.id],
            }
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.editor.profile.favourites.count(), 0)

    def test_bulk_status_change_on_permitted_items(self):
        self.login_registrar()
        self.item1.readyToReview = True
        self.item2.readyToReview = True
        self.item1.save()
        self.item2.save()

        self.assertTrue(perms.user_can_change_status(self.registrar, self.item1))
        self.assertFalse(self.item1.is_registered)
        response = self.client.post(
            reverse('aristotle:bulk_action'),
            {
                'bulkaction': 'change_state',
                'state': 1,
                'items': [self.item1.id, self.item2.id],
                'registrationDate': "2014-10-27",
                'cascadeRegistration': 0,
                'registrationAuthorities': [self.ra.id],
                'confirmed': 'confirmed',
            }
        )
        self.assertTrue(self.item1.is_registered)
        self.assertTrue(self.item2.is_registered)

    def test_bulk_status_change_on_forbidden_items(self):
        self.login_registrar()
        self.item1.readyToReview = True
        self.item4.readyToReview = True
        self.item1.save()
        self.item4.save()

        self.assertTrue(perms.user_can_change_status(self.registrar, self.item1))
        self.assertFalse(self.item1.is_registered)
        self.assertFalse(self.item2.is_registered)
        self.assertFalse(self.item4.is_registered)
        response = self.client.post(
            reverse('aristotle:bulk_action'),
            {
                'bulkaction': 'change_state',
                'state': 1,
                'items': [self.item1.id, self.item2.id, self.item4.id],
                'registrationDate': "2014-10-27",
                'cascadeRegistration': 0,
                'registrationAuthorities': [self.ra.id],
                'confirmed': 'confirmed',
            },
            follow=True
        )
        self.assertEqual(200, response.status_code)
        self.assertTrue(self.item1.is_registered)
        self.assertFalse(self.item2.is_registered)
        self.assertFalse(self.item4.is_registered)

        from django.utils.html import escape
        err1 = "Some items failed"
        err2 = "s: %s" % ','.join(sorted([str(self.item2.id), str(self.item4.id)]))

        self.assertTrue(err1 in response.content)
        self.assertTrue(err2 in response.content)
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertEqual(response.redirect_chain[0][1], 302)

    # TODO: bulk action *and* cascade, where a user doesn't have permission for child elements.
