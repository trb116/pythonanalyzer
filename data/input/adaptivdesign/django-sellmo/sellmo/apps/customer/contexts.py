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

from sellmo.core.local import LocalStorage


class ActiveCustomerGroupStorage(LocalStorage):
    def set_defaults(self):
        self.customer_group = None


class ActiveCustomerGroupHandle(object):

    _storage = ActiveCustomerGroupStorage()

    def __init__(self, customer_group):
        self.customer_group = customer_group

    def __enter__(self):
        self.previous_customer_group = self._storage.customer_group
        self._storage.customer_group = customer_group
        return self

    def __exit__(self, typ, value, traceback):
        self._storage.customer_group = self.previous_customer_group


class CustomerGroupContext(object):

    @classmethod
    def get_active(cls):
        if _storage.customer_group is not None:
            return _storage.customer_group

    def activate(*args, **kwargs):
        context = ActiveCustomerGroupHandle(self)
        return context


class ActiveAddressZonesStorage(LocalStorage):
    def set_defaults(self):
        self.zones = {}


class ActiveAddressZonesHandle(object):

    _storage = ActiveAddressZonesStorage()

    def __init__(self, *args, **kwargs):
        if len(args) > 1:
            raise ValueError("Zero or one zone expected")
        self.zones = dict(**kwargs)
        if args:
            self.zones[None] = args[0]

    def __enter__(self):
        self.previous_zones = dict(**self._storage.zones)
        self._storage.zones.update(self.zones)
        return self

    def __exit__(self, typ, value, traceback):
        self._storage.zones = self.previous_zones


class AddressZoneContext(object):

    @classmethod
    def get_active(cls, address_type=None):
        if address_type in _storage.zones:
            return _storage.zones[address_type]

    @classmethod
    def activate(cls, *args, **kwargs):
        context = ActiveAddressZonesHandle(*args, **kwargs)
        return context
