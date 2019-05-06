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

from sellmo.core.registry.inject import inherit_class, inherit_model

import sellmo.apps.customer as _customer


def CustomerForm(value): # NOQA
    class CustomerForm(value):
        class Meta(value.Meta):
            model = _customer.models.Customer

    return CustomerForm


def ContactableForm(value): # NOQA
    class ContactableForm(value):
        class Meta(value.Meta):
            model = _customer.models.Contactable

    return ContactableForm


def AddressForm(value): # NOQA
    class AddressForm(value):
        class Meta(value.Meta):
            model = _customer.models.Address

    return AddressForm


_customer.forms['CustomerForm'].inject(CustomerForm)
_customer.forms['ContactableForm'].inject(ContactableForm)
_customer.forms['AddressForm'].inject(AddressForm)


def Address(value): # NOQA
    class Address(value):

        objects = _customer.models.AddressManager.from_queryset(
            _customer.models.AddressQuerySet)()

        class Meta(value.Meta):
            pass

    return Address


_customer.models['AddressQuerySet'].inject(inherit_class(
    lambda: _customer.models.AddresseeQuerySet,
))

_customer.models['AddressManager'].inject(inherit_class(
    lambda: _customer.models.AddresseeManager
))

_customer.models['Address'].inject(inherit_model(
    lambda: _customer.models.Addressee
))

_customer.models['Address'].inject(Address)


def Customer(value): # NOQA
    class Customer(value):

        objects = _customer.models.CustomerManager.from_queryset(
            _customer.models.CustomerQuerySet)()

        class Meta(value.Meta):
            pass

    return Customer


_customer.models['CustomerQuerySet'].inject(inherit_class(
    lambda: _customer.models.ContactableQuerySet,
    lambda: _customer.models.AddresseeQuerySet
))

_customer.models['CustomerManager'].inject(inherit_class(
    lambda: _customer.models.ContactableManager,
    lambda: _customer.models.AddresseeManager
))

_customer.models['Customer'].inject(inherit_model(
    lambda: _customer.models.Contactable,
    lambda: _customer.models.Addressee
))

_customer.models['Customer'].inject(Customer)
