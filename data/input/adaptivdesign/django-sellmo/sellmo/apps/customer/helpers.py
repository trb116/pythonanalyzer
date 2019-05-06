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

from django.utils.functional import cached_property

import sellmo.apps.customer as _customer

NO_DEFAULT = object()


class AddressHelper(object):

    _mutated_addresses = None

    def __init__(self, obj, fk):
        self._obj = obj
        self._fk = fk

    @cached_property
    def _addresses_queryset(self):
        return _customer.models.Address.objects.filter(**{self._fk: self._obj})

    def get(self, address_type, default=NO_DEFAULT):
        try:
            return self[address_type]
        except KeyError:
            if default is not NO_DEFAULT:
                return default
            raise

    def __getitem__(self, address_type):
        address = None
        if self._mutated_addresses is not None:
            address = self._mutated_addresses.get(address_type, None)
        else:
            try:
                address = self._addresses_queryset.get(
                    address_type=address_type)
            except self._addresses_queryset.model.DoesNotExist:
                pass

        if address is None:
            raise KeyError(address_type)

        return address

    def __setitem__(self, address_type, value):
        if self._mutated_addresses is None:
            self._mutated_addresses = {
                address.address_type: address
                for address in self._addresses_queryset
            }
        value.address_type = address_type
        self._mutated_addresses[address_type] = value

    def __delitem__(self, address_type):
        if self._mutated_addresses is None:
            self._mutated_addresses = {
                address.address_type: address
                for address in self._addresses_queryset
            }
        del self._mutated_addresses[address_type]

    def __contains__(self, address_type):
        if self._mutated_addresses is not None:
            return address_type in self._mutated_addresses
        else:
            return self._addresses_queryset.filter(
                address_type=address_type).count() == 1

    def __iter__(self):
        addresses = self._addresses_queryset
        if self._mutated_addresses is not None:
            addresses = self._mutated_addresses.values()

        for address in addresses:
            yield address

    def __len__(self):
        if self._mutated_addresses is not None:
            return len(self._mutated_addresses)
        else:
            return self._addresses_queryset.count()

    def save_or_delete_addresses(self):
        if self._mutated_addresses is not None:
            for address in self._mutated_addresses.values():
                setattr(address, self._fk, self._obj)
                address.save()
            stale = self._addresses_queryset.exclude(
                pk__in=[
                    address.pk for address in self._mutated_addresses.values()
                ]
            )
            stale.delete()

        self._mutated_addresses = None
        try:
            del self._addresses_queryset
        except AttributeError:
            pass
