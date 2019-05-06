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
from sellmo.contrib.discount.constants import APPLIES_TO_CHOICES

from django.db import models
from django.db.models import Q
from django.contrib.sites.models import Site
from django.utils.translation import ugettext_lazy as _

import polymorphism

import sellmo.contrib.discount as _discount
import sellmo.apps.product as _product


@load(action='finalize_discount_Discount')
def finalize_model():
    class Discount(_discount.models.Discount):

        objects = (
            _discount.models.DiscountManager.from_queryset(
                _discount.models.DiscountQuerySet
            )
        )()

        class Meta(_discount.models.Discount.Meta):
            app_label = 'discount'

    _discount.models.Discount = Discount


@load(after='finalize_product_ProductRelatable')
@load(before='finalize_discount_Discount')
def load_model():
    class DiscountQuerySet(
        _discount.models.DiscountQuerySet,
        _product.models.ProductRelatableQuerySet
    ):
        pass

    class DiscountManager(
        _discount.models.DiscountManager,
        _product.models.ProductRelatableManager
    ):
        pass

    class Discount(
        _discount.models.Discount, _product.models.ProductRelatable
    ):
        class Meta(
            _discount.models.Discount.Meta,
            _product.models.ProductRelatable.Meta
        ):
            abstract = True

    _discount.models.Discount = Discount
    _discount.models.DiscountQuerySet = DiscountQuerySet
    _discount.models.DiscountManager = DiscountManager


class DiscountQuerySet(polymorphism.PolymorphicQuerySet):
    pass


class DiscountManager(polymorphism.PolymorphicManager):
    def get_by_natural_key(self, name):
        return self.get(name=name)


class Discount(polymorphism.PolymorphicModel):

    SUBTYPES = []

    name = models.CharField(max_length=80, verbose_name=_("name"), unique=True)

    customer_groups = models.ManyToManyField(
        'customer.CustomerGroup',
        blank=True,
        related_name='discounts',
    )

    applies_to = models.CharField(
        max_length=30,
        choices=APPLIES_TO_CHOICES,
        verbose_name=_("applies to")
    )

    active = models.BooleanField(default=True, verbose_name=_("active"))

    valid_from = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("valid from")
    )

    valid_to = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("valid to")
    )

    def natural_key(self):
        return (self.name, )

    def apply(self, price):
        raise NotImplementedError()

    def __unicode__(self):
        return self.name

    class Meta:
        abstract = True
        verbose_name = _("discount")
        verbose_name_plural = _("discounts")
