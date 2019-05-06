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
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from sellmo.core.loading import load
from sellmo.apps.pricing import Price, PriceField
from sellmo.utils.tracking import (
    TrackableQuerySet, TrackableManager, TrackableModel
)

import sellmo.apps.cart as _cart
import sellmo.apps.purchase as _purchase


class CartQuerySet(TrackableQuerySet):
    pass


class CartManager(TrackableManager):
    pass


class Cart(TrackableModel):

    _session_key = 'sellmo_cart'
    _mutated_purchases = None

    created = models.DateTimeField(auto_now_add=True, editable=False)

    modified = models.DateTimeField(auto_now=True, editable=False)

    calculated = models.DateTimeField(editable=False)

    subtotal = PriceField(verbose_name=_("subtotal"))

    total = PriceField(verbose_name=_("total"))

    def has_changed(self):
        return self._mutated_purchases is not None

    def needs_calculation(self):
        return (
            self.calculated is None or any(
                [
                    purchase.needs_calculation() for purchase in self
                ]
            )
        )

    def calculate(self):
        subtotal = Price(0)

        recalculated = False
        for purchase in self:
            if purchase.needs_calculation():
                recalculated |= purchase.calculate()
            if purchase.total is not None:
                subtotal += purchase.total

        if recalculated:
            self._mutate_purchases()

        total = Price.calculate.with_result(subtotal)(cart=self)

        recalculated |= subtotal != self.subtotal or total != self.total
        self.subtotal = subtotal
        self.total = total
        self.calculated = timezone.now()
        return recalculated

    def invalidate(self):
        try:
            del self._purchases_queryset
        except AttributeError:
            pass
        self.calculated = None
        self.subtotal = None
        self.total = None

    def _merge(self, purchase):
        try:
            mergeable = self._purchases_queryset.mergeable_with(purchase)
        except _purchase.models.Purchase.DoesNotExist:
            return None
        else:
            return purchase.merge(mergeable)

    def add(self, purchase):
        self._mutate_purchases()

        merged = self._merge(purchase)
        if merged is not None:
            purchase, stale_purchase = merged
            self._mutated_purchases.remove(stale_purchase)

        self._mutated_purchases.append(purchase)
        self.invalidate()

    def update(self, purchase):
        self._mutate_purchases()

        merged = self._merge(purchase)
        if merged is not None:
            purchase, stale_purchase = merged
            self._mutated_purchases.remove(stale_purchase)

        # Replace the persisted purchase (identified by pk) with
        # an (most likely) changed instance.
        idx = self._mutated_purchases.index(purchase)
        self._mutated_purchases[idx] = purchase
        self.invalidate()

    def remove(self, purchase):
        self._mutate_purchases()
        self._mutated_purchases.remove(purchase)
        self.invalidate()

    def clear(self):
        self._mutated_purchases = []
        self.invalidate()

    def save(self, *args, **kwargs):
        super(Cart, self).save(*args, **kwargs)

        if self._mutated_purchases is not None:
            for purchase in self._mutated_purchases:
                purchase.cart = self
                purchase.save()
            stale = self.purchases.exclude(
                pk__in=[
                    purchase.pk for purchase in self._mutated_purchases
                ]
            )
            stale.delete()

        self._mutated_purchases = None
        try:
            del self._purchases_queryset
        except AttributeError:
            pass

    @cached_property
    def _purchases_queryset(self):
        return self.purchases.polymorphic().all()

    def _mutate_purchases(self):
        if self._mutated_purchases is None:
            self._mutated_purchases = list(self._purchases_queryset)

    def __contains__(self, purchase):
        if self._mutated_purchases is not None:
            return purchase in self._mutated_purchases
        return purchase.cart == self

    def __iter__(self):
        purchases = self._purchases_queryset
        if self._mutated_purchases is not None:
            purchases = self._mutated_purchases

        for purchase in purchases:
            yield purchase

    def __len__(self):
        if self._mutated_purchases is not None:
            return len(self._mutated_purchases)
        return self._purchases_queryset.count()

    def __nonzero__(self):
        return len(self) > 0

    def __unicode__(self):
        return unicode(self.modified)

    class Meta:
        abstract = True
        app_label = 'cart'
        verbose_name = _("cart")
        verbose_name_plural = _("carts")
        ordering = ['-pk']
