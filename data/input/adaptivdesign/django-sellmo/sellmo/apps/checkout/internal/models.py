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
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _


from sellmo.apps.pricing import Price, PriceField
from sellmo.apps.customer.helpers import AddressHelper

from ..exceptions import OrderStateInvalid, OrderFlowInvalid
from ..signals import (
    order_placed, order_paid, order_completed, order_closed, order_cancelled,
    order_state_changed, order_status_changed
)
from ..constants import (
    ORDER_STATE_UNPLACED, ORDER_STATE_PLACED, ORDER_STATE_COMPLETED,
    ORDER_STATE_CANCELLED, ORDER_STATE_CLOSED, ORDER_STATUSES,
    CUSTOMER_REQUIRED
)

import sellmo.apps.checkout as _checkout
import sellmo.apps.customer as _customer

class OrderQuerySet(models.QuerySet):
    pass


class OrderManager(models.Manager):
    pass


class Order(models.Model):

    _mutated_purchases = None

    def __init__(self, *args, **kwargs):
        super(Order, self).__init__(*args, **kwargs)
        self.addresses = AddressHelper(self, 'order')

    @staticmethod
    def generate_order_number(order):
        return unicode(order.pk)

    @classmethod
    def from_request(cls, request):
        cart = _cart.models.from_request(request)
        if cart is None or not hasattr(cart, 'order'):
            order = cls()
            order.cart = cart
        else:
            order = cart.order

        if order.needs_calculation():
            order.calculate()

        return order

    number = models.CharField(
        max_length=80,
        blank=True,
        verbose_name=_("order number"),
    )

    created = models.DateTimeField(auto_now_add=True, editable=False)

    modified = models.DateTimeField(auto_now=True, editable=False)

    calculated = models.DateTimeField(editable=False)

    state = models.CharField(
        max_length=20,
        editable=False,
        default=ORDER_STATE_UNPLACED
    )

    customer = models.ForeignKey(
        'customer.Customer',
        null=not CUSTOMER_REQUIRED,
        blank=not CUSTOMER_REQUIRED,
        related_name='orders',
        verbose_name=_("customer"),
    )

    status = models.CharField(
        max_length=40,
        default=ORDER_STATUSES.initial,
        choices=ORDER_STATUSES.choices,
        verbose_name=_("status"),
    )

    cart = models.OneToOneField(
        'cart.Cart',
        related_name='order',
        editable=False,
        null=True,
        on_delete=models.PROTECT
    )

    subtotal = PriceField(verbose_name=_("subtotal"))

    total = PriceField(verbose_name=_("total"))

    paid = PriceField(default=0, components=None, verbose_name=_("paid"))

    def add(self, purchase):
        self._mutate_purchases()
        self._mutated_purchases.append(purchase)
        self.invalidate()

    def update(self, purchase):
        self._mutate_purchases()
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

    def needs_calculation(self):
        return (
            self.may_change and self.calculated is None or any(
                [
                    purchase.needs_calculation() for purchase in self
                ]
            )
        )

    def calculate(self):

        zones = {}
        for address in self.addresses:
            zones[address.address_type] = address.get_zone()

        with _customer.models.AddressZone.activate_zones(**zones):

            self._ensure_state(ORDER_STATE_UNPLACED)
            subtotal = Price(0)

            recalculated = False
            for purchase in self:
                # If we calculate order, we always calculate the purchase
                recalculated |= purchase.calculate()
                if purchase.total is not None:
                    subtotal += purchase.total

            # In case our purchases do not belong to a cart and recalculation
            # is required, then it's our responsibility to calculate AND save
            # the purchases. If purchases belong to a cart, then ONLY
            # recalculate the purchases in order to get a correct total.
            if recalculated and self.cart is None:
                self._mutate_purchases()

            subtotal = Price.calculate.with_result(subtotal)(subtotal=True, order=self)
            total = Price.calculate.with_result(subtotal)(total=True, order=self)

        recalculated |= subtotal != self.subtotal or total != self.total
        self.subtotal = subtotal
        self.total = total
        self.calculated = timezone.now()
        return recalculated

    def invalidate(self):
        self._ensure_state(ORDER_STATE_UNPLACED)

        try:
            del self._purchases_queryset
        except AttributeError:
            pass

        self.number = ''
        self.total = None
        self.subtotal = None
        self.calculated = None

    def place(self):
        self._ensure_state(ORDER_STATE_UNPLACED)
        self.number = self.generate_order_number(self)
        self.state = ORDER_STATE_PLACED

    def cancel(self):
        self.state = ORDER_STATE_CANCELLED

    @property
    def is_unplaced(self):
        return self.state == ORDER_STATE_UNPLACED

    @property
    def is_placed(self):
        return self.state == ORDER_STATE_PLACED

    @property
    def is_completed(self):
        return self.state == ORDER_STATE_COMPLETED

    @property
    def is_closed(self):
        return self.state == ORDER_STATE_CLOSED

    @property
    def is_cancelled(self):
        return self.state == ORDER_STATE_CANCELLED

    @property
    def may_cancel(self):
        return self.is_placed and not self.paid.amount

    @property
    def may_change(self):
        return self.state == ORDER_STATE_UNPLACED

    @property
    def is_paid(self):
        return self.total.amount == self.paid.amount

    @property
    def remaining(self):
        return self.total - self.paid

    def can_change_status(self, status):
        can_change = False

        # Verify new status
        if status not in ORDER_STATUSES:
            raise ValueError(status)

        # Lookup current status
        entry = ORDER_STATUSES[self.status]
        config = entry[1] if len(entry) == 2 else {}
        if 'flow' in config:
            # Check against flow
            if status in config['flow']:
                can_change = True
        return can_change

    def clean(self):
        old = None
        if self.pk:
            old = type(self).objects.get(pk=self.pk)
        if old is not None and self.status != old.status:
            if not old.can_change_status(self.status):
                raise ValidationError(
                    "Cannot transition order status "
                    "from '{0}' to '{1}'".format(old.status, self.status)
                )

    def save(self, *args, **kwargs):

        old = None
        if self.pk:
            old = type(self).objects.get(pk=self.pk)

        # See if status is explicitly changed
        if old is not None and self.status != old.status:
            # Make sure this change is a valid flow
            if not old.can_change_status(self.status):
                raise OrderFlowInvalid()

        # Check for new status
        status_changed = (
            old is None and self.status != ORDER_STATUSES.initial or
            old is not None and self.status != old.status
        )

        # Check for new state
        state_changed = (
            old is None and self.state != ORDER_STATE_UNPLACED or
            old is not None and self.state != old.state
        )

        # Check for now paid
        now_paid = (old is None or not old.is_paid) and self.is_paid

        # Get new status from new state
        if (
            not status_changed and state_changed and
            'on_{0}'.format(self.state) in ORDER_STATUSES.hook_to_status
        ):
            self.status = ORDER_STATUSES.hook_to_status['on_{0}'.format(
                self.state)]

        # Get new status from on_paid
        if (
            not status_changed and now_paid and
            'on_paid' in ORDER_STATUSES.hook_to_status
        ):
            self.status = ORDER_STATUSES.hook_to_status['on_paid']

        # Get new state from new status
        if (
            not state_changed and status_changed and
            self.status in ORDER_STATUSES.status_to_state
        ):
            self.state = ORDER_STATUSES.status_to_state[self.status]

        # Check for new status (again)
        status_changed = old is None or self.status != old.status

        # Check for new state (again)
        state_changed = old is None or self.state != old.state

        cart = None
        if state_changed and self.state == ORDER_STATE_PLACED:
            cart = self.cart
            self.cart = None

        # At this point we save
        super(Order, self).save(*args, **kwargs)

        if cart is not None:
            # The order has been placed, we'll want to move over
            # purchases from cart.
            cart.purchases.update(cart=None, order=self)
            cart.delete()

        # Handle mutated purchases in case this order was directly created
        # or modified.
        if self._mutated_purchases is not None:
            for purchase in self._mutated_purchases:
                purchase.order = self
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

        # Save addresses
        self.addresses.save_or_delete_addresses()

        # Finally signal
        if status_changed:
            order_status_changed.send(
                sender=self,
                order=self,
                new_status=self.status,
                old_status=old.status if old is not None else None
            )

        if state_changed:
            order_state_changed.send(
                sender=self,
                order=self,
                new_state=self.state,
                old_state=old.state if old is not None else None
            )

            # Handle shortcuts
            if self.state == ORDER_STATE_PLACED:
                order_placed.send(sender=self, order=self)
            elif self.state == ORDER_STATE_COMPLETED:
                order_completed.send(sender=self, order=self)
            elif self.state == ORDER_STATE_CANCELLED:
                order_cancelled.send(sender=self, order=self)
            elif self.state == ORDER_STATE_CLOSED:
                order_closed.send(sender=self, order=self)

        if now_paid:
            order_paid.send(sender=self, order=self)

    @cached_property
    def _purchases_queryset(self):
        return self.purchases.polymorphic().all()

    def _ensure_state(self, state):
        if self.state != state:
            raise OrderStateInvalid("State '{0}' expected".format(state))

    def _mutate_purchases(self):
        if self.cart is not None:
            raise Exception("Cannot mutate purchases belonging to cart.")
        if self._mutated_purchases is None:
            self._mutated_purchases = list(self._purchases_queryset)

    def __contains__(self, purchase):
        if self.cart is not None:
            return purchase in self.cart
        elif self._mutated_purchases is not None:
            return purchase in self._mutated_purchases
        return purchase.order == self

    def __iter__(self):
        purchases = self._purchases_queryset
        if self.cart is not None:
            purchases = self.cart
        elif self._mutated_purchases is not None:
            purchases = self._mutated_purchases

        for purchase in purchases:
            yield purchase

    def __len__(self):
        if self.cart is not None:
            return len(self.cart)
        elif self._mutated_purchases is not None:
            return len(self._mutated_purchases)
        return self._purchases_queryset.count()

    def __nonzero__(self):
        return len(self) > 0

    def __unicode__(self):
        if self.number:
            return unicode(_(u"order #{0}").format(unicode(self.number)))
        else:
            return unicode(_(u"unplaced order"))

    class Meta:
        abstract = True
        verbose_name = _("order")
        verbose_name_plural = _("orders")
        ordering = ['-pk']
