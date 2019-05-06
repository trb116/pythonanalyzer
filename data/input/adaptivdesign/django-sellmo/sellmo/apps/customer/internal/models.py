# Copyright (c) 2014, Adaptiv Design
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.

# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.

# 3. Neither the name of the copyright holder nor the names of its contributors
# may be used to endorse or promote products derived from this software without
# specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

from django.db import models
from django.utils.translation import ugettext_lazy as _

from sellmo.core.loading import load
from sellmo.utils.cloning import Cloneable

from ..helpers import AddressHelper
from ..contexts import CustomerGroupContext, AddressZoneContext
from ..constants import (
    BUSINESSES_ALLOWED, BUSINESSES_ONLY, ADDRESS_TYPES, EMAIL_REQUIRED
)

import sellmo.apps.customer as _customer


class CustomerQuerySet(models.QuerySet):
    pass


class CustomerManager(models.Manager):
    pass


class Customer(models.Model, Cloneable):
    def __init__(self, *args, **kwargs):
        super(Customer, self).__init__(*args, **kwargs)
        self.addresses = AddressHelper(self, 'customer')

    group = models.ForeignKey(
        'customer.CustomerGroup',
        blank=True,
        null=True,
        verbose_name=_("customer group")
    )

    @classmethod
    def from_request(cls, request):
        return None

    def save(self, *args, **kwargs):
        super(Customer, self).save(*args, **kwargs)
        self.addresses.save_or_delete_addresses()

    def clone(self, cls=None, clone=None):
        clone = super(Customer, self).clone(cls=cls, clone=clone)
        clone.group = self.group
        for address_type, address in self.addresses:
            clone.addresses[address_type] = address.clone()

        return clone

    class Meta:
        abstract = True
        app_label = 'customer'
        verbose_name = _("customer")
        verbose_name_plural = _("customers")


class CustomerGroupQuerySet(models.QuerySet):
    pass


class CustomerGroupManager(models.Manager):
    pass


class CustomerGroup(CustomerGroupContext, models.Model):

    name = models.CharField(max_length=80, verbose_name=_("name"), unique=True)

    default = models.BooleanField(default=False, verbose_name=_("default"))

    unknown = models.BooleanField(default=False, verbose_name=_("unknown"))

    @classmethod
    def from_request(request):
        customer = _customer.models.Customer.from_request(request)
        if customer is not None:
            return customer.group

    def __unicode__(self):
        return self.name

    class Meta:
        abstract = True
        verbose_name = _("customer group")
        verbose_name_plural = _("customer groups")
        ordering = ['name']


class AddressQuerySet(models.QuerySet):
    pass


class AddressManager(models.Manager):
    pass


class Address(models.Model, Cloneable):

    address_type = models.CharField(
        max_length=20,
        choices=[
            (address_type, address_type) for address_type in ADDRESS_TYPES
        ],
        verbose_name=_("address type")
    )

    customer = models.ForeignKey(
        'customer.Customer',
        null=True,
        related_name='customer_addresses',
        editable=False
    )

    def get_zone(self):
        return _customer.models.AddressZone()

    def clone(self, cls=None, clone=None):
        clone = super(Address, self).clone(cls=cls, clone=clone)
        return clone

    class Meta:
        abstract = True
        verbose_name = _("address")
        verbose_name_plural = _("addresses")


class ContactableQuerySet(models.QuerySet):
    pass


class ContactableManager(models.Manager):
    pass


class Contactable(models.Model, Cloneable):

    email = models.EmailField(
        blank=not EMAIL_REQUIRED,
        verbose_name=_("email address"),
    )

    def clone(self, cls=None, clone=None):
        clone = super(Contactable, self).clone(cls=cls, clone=clone)
        clone.email = self.email
        return clone

    class Meta:
        abstract = True


class AddresseeQuerySet(models.QuerySet):
    pass


class AddresseeManager(models.Manager):
    pass


class Addressee(models.Model, Cloneable):

    first_name = models.CharField(max_length=30, verbose_name=_("first name"))

    last_name = models.CharField(max_length=30, verbose_name=_("last name"))

    if BUSINESSES_ALLOWED:
        company_name = models.CharField(
            max_length=50,
            verbose_name=_("company name"),
            blank=not BUSINESSES_ONLY,
        )

        @property
        def is_business(self):
            return bool(self.company_name)
    else:

        @property
        def is_business(self):
            return False

    def clone(self, cls=None, clone=None):
        clone = super(Addressee, self).clone(cls=cls, clone=clone)
        clone.first_name = self.first_name
        clone.last_name = self.last_name
        if BUSINESSES_ALLOWED:
            clone.company_name = self.company_name
        return clone

    def __unicode__(self):
        return u"{0} {1}".format(self.first_name, self.last_name)

    class Meta:
        abstract = True
        ordering = ['last_name', 'first_name']


class AddressZoneQuerySet(models.QuerySet):

    def spans(self, zone):
        return self.all()


class AddressZoneManager(models.Manager):
    pass


class AddressZone(AddressZoneContext, models.Model):

    @classmethod
    def from_request(cls, request, address_type=None):
        return None

    def spans(self, other):
        return True

    class Meta:
        abstract = True
