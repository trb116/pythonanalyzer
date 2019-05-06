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
from sellmo.contrib.settings import settings_manager

from .constants import (
    PHONE_NUMBER_ENABLED, NAME_PREFIX_ENABLED, NAME_SUFFIX_ENABLED,
    PHONE_NUMBER_REQUIRED, NAME_PREFIX_REQUIRED
)

import sellmo.apps.customer as _customer


@load(before='finalize_customer_AddressZone')
def load_model():
    class AddressZone(_customer.models.AddressZone):
        @classmethod
        def get_default(cls, address_type=None):
            zone = settings_manager['default_address_zone']
            if zone is None:
                zone = super(AddressZone, cls).get_default(address_type)
            return zone

        class Meta(_customer.models.AddressZone.Meta):
            abstract = True

    _customer.models.AddressZone = AddressZone


@load(before='finalize_customer_Addressee')
def load_model():
    class Addressee(_customer.models.Addressee):

        if NAME_PREFIX_ENABLED:
            prefix = models.CharField(
                max_length=20,
                verbose_name=_("prefix"),
                blank=not NAME_PREFIX_REQUIRED,
                choices=NAME_PREFIX_CHOICES,
                default=NAME_PREFIX_CHOICES[0][0]
            )

        if NAME_SUFFIX_ENABLED:
            suffix = models.CharField(
                max_length=10,
                blank=True,
                verbose_name=_("suffix"),
            )

        def clone(self, cls=None, clone=None):
            clone = super(Addressee, self).clone(cls=cls, clone=clone)
            if NAME_SUFFIX_ENABLED:
                clone.suffix = self.suffix
            if NAME_PREFIX_ENABLED:
                clone.prefix = self.prefix
            return clone

        class Meta(_customer.models.Addressee.Meta):
            abstract = True

    _customer.models.Addressee = Addressee


@load(before='finalize_customer_Contactable')
def load_model():
    class Contactable(_customer.models.Contactable):

        if PHONE_NUMBER_ENABLED:
            phone_number = models.CharField(
                max_length=20,
                blank=not PHONE_NUMBER_REQUIRED,
                verbose_name=_("phone number"),
            )

        def clone(self, cls=None, clone=None):
            clone = super(Contactable, self).clone(cls=cls, clone=clone)
            if PHONE_NUMBER_ENABLED:
                clone.phone_number = self.phone_number
            return clone

        class Meta(_customer.models.Contactable.Meta):
            abstract = True

    _customer.models.Contactable = Contactable
