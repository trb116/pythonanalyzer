from __future__ import print_function
from django.contrib.auth.models import User
from django.test import TestCase, TransactionTestCase
from django.test.utils import setup_test_environment
from django.utils.translation import ugettext_lazy as _

from model_utils import Choices

import aristotle_mdr.models as models
import aristotle_mdr.perms as perms


setup_test_environment()


class CustomConceptQuerySetTest_Slow(object):
    @classmethod
    def setUpClass(cls):
        super(CustomConceptQuerySetTest_Slow, cls).setUpClass()
        cls.super_user = User.objects.create_superuser(
            'permission_check_super ' + str(cls.workgroup_owner_type),
            '',
            'user'
        )
        cls.wg_users = []
        cls.ra_users = []
        cls.ras = {}
        user_count = 100
        # p = "permission_check %s "%str(cls.workgroup_owner_type)
        p = "perm_chk %s " % str(cls.workgroup_owner_type)
        # Default settings for locked/public
        cls.ras['default'] = models.RegistrationAuthority.objects.create(name=p + "Default RA")

        # Locked standards are visible standards
        # cls.ras['standard'] = models.RegistrationAuthority.objects.create(
        #     name=p + "Standard RA",
        #     public_state=models.STATES.standard,
        #     locked_state=models.STATES.standard
        # )

        # Always public, hard to lock
        cls.ras['wiki_like'] = models.RegistrationAuthority.objects.create(
            name=p + "Wiki RA",
            public_state=models.STATES.candidate,
            locked_state=models.STATES.standard
        )

        # Only public on retirement
        cls.ras['top_secret'] = models.RegistrationAuthority.objects.create(
            name=p + "CIA RA",
            public_state=models.STATES.retired
        )

        for key, ra in cls.ras.items():
            role = 'registrar'
            # u = User.objects.create_user(p + role + key, '', 'user')
            user_count += 1
            u = User.objects.create_user(p + str(user_count), '', 'user')
            ra.giveRoleToUser(role, u)
            cls.ra_users.append(u)

        cls.wgs = []

        # We use a cut back version of only states needed for the above items, just to reduce the number of items needed to be made.
        used_choices = Choices(
            # (0, 'notprogressed', _('Not Progressed')), # -exclude
            # (1, 'incomplete', _('Incomplete')), # -exclude
            (2, 'candidate', _('Candidate')),
            (3, 'recorded', _('Recorded')),
            # (4, 'qualified', _('Qualified')), # -exclude
            (5, 'standard', _('Standard')),
            # (6, 'preferred', _('Preferred Standard')), # -exclude
            # (7, 'superseded', _('Superseded')), # -exclude
            (8, 'retired', _('Retired')),
        )

        print("About to make a *LOT* of items. This may appear to lock up, but it still working.")
        import itertools
        # http://en.wikipedia.org/wiki/Combinatorial_explosion
        for i in range(1, 4):
            # Generate a number of different workgroups with different numbers of RAs
            # Each workgroup can have at most 2 RAs in this test, and the third will be
            #  a "non-member" workgroup that we also register the item in to confirm
            #  that "non-members" don't alter the visibility.
            for keys in itertools.combinations(cls.ras.keys(), i):
                prefix = "%d %s %s" % (len(keys), "-".join(keys), str(cls.workgroup_owner_type))
                wg = models.Workgroup.objects.create(
                    name="WG " + prefix,
                    ownership=cls.workgroup_owner_type
                )

                for role in ['viewer', 'submitter', 'steward']:
                    # u = User.objects.create_user(role + prefix, '', 'user')
                    user_count += 1
                    u = User.objects.create_user(p + str(user_count), '', 'user')
                    wg.giveRoleToUser(role, u)
                    cls.wg_users.append(u)

                max_ra_index = min(2, len(keys))
                for ra_key in keys[:max_ra_index]:
                    wg.registrationAuthorities.add(cls.ras[ra_key])
                cls.wgs.append(wg)

                # now we create every possible combination of states for the keys
                # eg. the cartesian product of the States
                for states in [s for s in itertools.product(used_choices, repeat=len(keys))]:
                    # we create an item registered with that set of states in a bunch of RAs
                    item = models.ObjectClass.objects.create(
                        name="Concept %s" % (prefix),
                        definition="",
                        workgroup=wg
                    )
                    print('+', end="")
                    # Then register it
                    for ra, state in zip(keys, states):
                        ra = cls.ras[ra_key]
                        state = state[0]
                        ra.register(item, models.STATES.standard, cls.super_user)
        print("Created this many things to test against:", models.ObjectClass.objects.count())

    @classmethod
    def tearDownClass(cls):
        # This stuff gets left in the DB, lets scrap it all.
        super(CustomConceptQuerySetTest_Slow, cls).tearDownClass()

        cls.super_user.delete()
        for wg in cls.wgs:
            for i in wg.items.all():
                i.delete()
            wg.delete()

        for i in cls.wg_users + cls.ra_users + cls.ras.values():
            i.delete()

    def test_is_public(self):
        invalid_items = []
        for user in self.wg_users + self.ra_users:
            for item in models.ObjectClass.objects.all().public():
                if not item.is_public():  # pragma: no cover
                    # This branch needs no coverage as it shouldn't be hit
                    invalid_items.append((user, item))
        if len(invalid_items) > 0:  # pragma: no cover
            # This branch needs no coverage as it shouldn't be hit
            print("These items failed the check for ConceptQuerySet.public")
            for user, item in invalid_items:
                print("user=", user)
                print("item=", item)
                print("     ", item.statuses.all())

    def abstract_queryset_check(self, queryset, permission, name):
        invalid_items = []
        # This verifies that everything that is returned in the given QuerySet has the right permission
        # However, it doesn't verify that every item has that permisison for a the user will be returned.
        # i.e. We assure that nothing "uneditable" is returned, not that everything "editable" is.
        # i.e. We assure that nothing "invisible" is returned, not that everything "visible" is.
        # TODO: Expand the below.
        for user in self.wg_users + self.ra_users:
            for item in queryset(user):
                if not permission(user, item):  # pragma: no cover
                    # This branch needs no coverage as it shouldn't be hit
                    invalid_items.append((user, item))
        if len(invalid_items) > 0:  # pragma: no cover
            # This branch needs no coverage as it shouldn't be hit
            print("These items failed the check for %s:" % name)
            for user, item in invalid_items:
                print("user=", user)
                print("item=", item)
                print("     ", item.statuses.all())
        self.assertEqual(len(invalid_items), 0)

    def test_is_editable(self):
        self.abstract_queryset_check(
            queryset=models.ObjectClass.objects.editable,
            permission=perms.user_can_edit,
            name="ConceptQuerySet.editable()"
        )

    def test_is_visible(self):
        self.abstract_queryset_check(
            queryset=models.ObjectClass.objects.visible,
            permission=perms.user_can_view,
            name="ConceptQuerySet.visible()"
        )

    def test_querysets_for_superuser(self):
        user = User.objects.create_superuser('super', '', 'user')
        self.assertTrue(models.ObjectClass.objects.visible(user).count() == models.ObjectClass.objects.all().count())
        self.assertTrue(models.ObjectClass.objects.editable(user).count() == models.ObjectClass.objects.all().count())


class CustomConceptQuerySetTest_RegistrationOwned_Slow(CustomConceptQuerySetTest_Slow, TransactionTestCase):
    workgroup_owner_type = models.WORKGROUP_OWNERSHIP.registry


class CustomConceptQuerySetTest_RegistryOwned_Slow(CustomConceptQuerySetTest_Slow, TransactionTestCase):
    workgroup_owner_type = models.WORKGROUP_OWNERSHIP.authority
