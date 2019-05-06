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

from sellmo.core.loading import load
from sellmo.contrib.customer.fields import CountryField

from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _


class AddressZoneQuerySet(models.QuerySet):

    def spans(self, zone):
        q = (
            (Q(country=zone.country) | Q(country=''))
            & (Q(state=zone.state) | Q(state=''))
        )
        return (
            super(AddressZoneQuerySet, self).spans(zone).filter(q)
        )

    def for_default_address(self, address):
        return self.for_address(address)


class AddressZone(models.Model):

    state = models.CharField(
        max_length=80,
        blank=True,
        verbose_name=_("state")
    )

    postcode = models.CharField(
        max_length=30,
        blank=True,
        verbose_name=_("postcode")
    )

    country = CountryField(blank=True, verbose_name=_("country"))

    def spans(self, other):
        return (
            (self.country == other.country or self.country == '') and
            (self.state == other.state or self.state == '') and
            super(AddressZone, self).spans(other)
        )

    def __unicode__(self):
        return self.country

    class Meta:
        abstract = True


class Address(models.Model):

    line1 = models.CharField(
        max_length=80,
        verbose_name=_("address line 1")
    )

    line2 = models.CharField(
        max_length=80,
        blank=True,
        verbose_name=_("address line 2")
    )

    line3 = models.CharField(
        max_length=80,
        blank=True,
        verbose_name=_("address line 3")
    )

    city = models.CharField(max_length=80, verbose_name=_("city"))

    state = models.CharField(
        max_length=80,
        blank=True,
        verbose_name=_("state")
    )

    postcode = models.CharField(max_length=30, verbose_name=_("postcode"))

    country = CountryField(verbose_name=_("country"))

    def get_zone(self):
        zone = super(Address, self).get_zone()
        zone.country = self.country
        zone.state = self.state
        return zone

    def clone(self, cls=None, clone=None):
        clone = super(Address, self).clone(cls=cls, clone=clone)
        clone.line1 = self.line1
        clone.line2 = self.line2
        clone.line3 = self.line3
        clone.city = self.city
        clone.state = self.state
        clone.postcode = self.postcode
        clone.country = self.country

        return clone

    class Meta:
        abstract = True
