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

from sellmo.apps.pricing import PriceField
from sellmo.core.loading import load

from django.db import models
from django.contrib.sites.models import Site
from django.utils.translation import ugettext_lazy as _

import polymorphism

import sellmo.contrib.shipping as _shipping


@load(action='finalize_shipping_ShippingMethod')
def finalize_model():
    class ShippingMethod(_shipping.models.ShippingMethod):

        objects = _shipping.models.ShipmentManager.from_queryset(
            _shipping.models.ShipmentQuerySet)()

        class Meta(_shipping.models.ShippingMethod.Meta):
            app_label = 'shipping'

    _shipping.models.ShippingMethod = ShippingMethod


class ShippingMethodQuerySet(models.QuerySet):
    pass


class ShippingMethodManager(models.Manager):
    pass


class ShippingMethod(polymorphism.PolymorphicModel):

    active = models.BooleanField(default=True, verbose_name=_("active"))

    identifier = models.CharField(
        unique=True,
        db_index=True,
        max_length=20,
        verbose_name=_("identifier")
    )

    name = models.CharField(max_length=80, verbose_name=_("name"))

    carriers = models.ManyToManyField(
        'shipping.ShippingCarrier',
        blank=True,
        verbose_name=_("carriers")
    )

    def get_methods(self):
        if self.carriers.count() == 0:
            yield self.get_method()
        else:
            for carrier in self.carriers.all():
                yield self.get_method(carrier)

    def get_method(self, carrier=None):
        from .method import ShippingMethod
        return ShippingMethod(self.identifier, self.name, carrier=carrier)

    def __unicode__(self):
        return self.name

    class Meta:
        abstract = True
        verbose_name = _("shipping method")
        verbose_name_plural = _("shipping methods")


@load(action='finalize_shipping_ShippingCarrier')
def finalize_model():
    class ShippingCarrier(_shipping.models.ShippingCarrier):

        objects = _shipping.models.ShipmentManager.from_queryset(
            _shipping.models.ShipmentQuerySet)()

        class Meta(_shipping.models.ShippingCarrier.Meta):
            app_label = 'shipping'

    _shipping.models.ShippingCarrier = ShippingCarrier


class ShippingCarrierQuerySet(models.QuerySet):
    pass


class ShippingCarrierManager(models.Manager):
    pass


class ShippingCarrier(models.Model):

    active = models.BooleanField(default=True, verbose_name=_("active"))

    identifier = models.CharField(
        unique=True,
        db_index=True,
        max_length=20,
        verbose_name=_("identifier")
    )

    name = models.CharField(max_length=80, verbose_name=_("name"))

    extra_costs = PriceField(
        multi_currency=True,
        components=None,
        verbose_name=_("extra_costs")
    )

    def __unicode__(self):
        return self.name

    class Meta:
        abstract = True
        verbose_name = _("shipping carrier")
        verbose_name_plural = _("shipping carriers")


@load(action='finalize_shipping_Shipment')
def finalize_model():
    class Shipment(_shipping.models.Shipment):

        objects = _shipping.models.ShipmentManager.from_queryset(
            _shipping.models.ShipmentQuerySet)()

        class Meta(_shipping.models.Shipment.Meta):
            app_label = 'shipping'

    _shipping.models.Shipment = Shipment


class ShipmentQuerySet(polymorphism.PolymorphicQuerySet):
    pass


class ShipmentManager(polymorphism.PolymorphicManager):
    pass


class Shipment(polymorphism.PolymorphicModel):

    order = polymorphism.PolymorphicOneToOneField(
        'checkout.Order',
        null=True,
        related_name='order_shipment',
        polymorphic_related=True,
        editable=False
    )

    method_string = models.CharField(
        max_length=41, # ShippingMethod_max_length|ShippingCarrier_max_length
        editable=False)

    description = models.CharField(
        max_length=255,
        verbose_name=_("description")
    )

    costs = PriceField(default=0, verbose_name=_("costs"))

    def resolve_method(self):
        # If a shipment is subclassed it can resolve a method if desired.
        # Return None if method no longer is applicable.
        return NotImplemented

    def __unicode__(self):
        return self.description

    class Meta:
        abstract = True
        verbose_name = _("shipment")
        verbose_name_plural = _("shipments")
