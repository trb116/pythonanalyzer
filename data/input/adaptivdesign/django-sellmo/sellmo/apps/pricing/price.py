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

from decimal import Decimal

from sellmo.core import chaining

from django.utils import six

from .currency import Currency
from .exceptions import CurrencyMismatch, PriceComponentOverflow
from .utils import safe_decimal, merge_amount_dicts

__all__ = ['Price', 'PriceComponent']


class PriceComponent(object):

    key = None
    verbose_name = None

    extra_fields = None
    """
    A list with extra fields names
    to be taken into concideration
    when assigning, retrieving, or indexing.
    """

    multiplicity = 1
    """
    Number of times this component is represented
    in each model or index per price field.
    """

    def __init__(self, key=None, verbose_name=None, multiplicity=None):
        self.key = key or self.key
        self.verbose_name = verbose_name or self.verbose_name
        self.multiplicity = multiplicity or self.multiplicity
        self.extra_fields = self.extra_fields or []

    def extract_price(self, price):
        extracted = list(self.extract(price))
        if extracted:
            price = Price(0, currency=price.currency)
            for (amount, extra_values) in extracted:
                price.amount += amount
                price = self.apply(price, amount, extra_values)
            return price
        return None

    def safe_extract(self, price):
        extracted = list(self.extract(price))
        if len(extracted) > self.multiplicity:
            raise PriceComponentOverflow(self)

        if len(extracted) < self.multiplicity:
            empty_extra_values = self.empty_extra_values()
            for _ in range(len(extracted), self.multiplicity):
                extracted.append((None, empty_extra_values))

        return extracted

    def extract(self, price):
        """
        Finds and extracts component prices
        out of the given price. These should
        be outputted as (amount, extra_values)
        """
        raise NotImplementedError()

    def apply(self, price, amount, extra_values):
        """
        Opposite of extract. Can be called multiple
        times, depending on how many prices where
        extracted for this comonent.
        """
        raise NotImplementedError()

    def construct_extra_model_fields(self):
        """
        Returns a dictionary representing the
        extra fields as a model field.
        """
        return {}

    def construct_extra_index_fields(self):
        """
        Returns a dictionary representing the
        extra fields as an index field.
        """
        return {}

    def empty_extra_values(self):
        """
        Returns a dictionary of empty extra
        values. This will be used when multiplicity
        isn't fully used.
        """
        return {}

    def prepare_for_index(self, price, extra_values):
        return (price, extra_values)

    def prepare_from_index(self, price, extra_values):
        return (price, extra_values)

    def prepare_for_model(self, price, extra_values):
        return (price, extra_values)

    def prepare_from_model(self, price, extra_values):
        return (price, extra_values)

    def __repr__(self):
        return self.key


class Price(object):

    COMPONENTS = []

    def sanity_check(self, other):
        if not isinstance(other, Price):
            raise TypeError(other)
        if self.currency != other.currency:
            raise CurrencyMismatch(self, other)

    @staticmethod
    @chaining.define
    def calculate(currency=None, bare=False, **kwargs):
        if currency is None:
            currency = Currency.get_current()
            yield chaining.update(currency=currency)

        with currency.activate():
            yield chaining.forward

    def __init__(self, amount, currency=None, component=None):

        amount = safe_decimal(amount)

        if currency is None:
            currency = Currency.get_current()

        self.amount = amount
        self.currency = currency
        self.component = component

        components = {}
        if self.component:
            components[self.component] = amount
        self.components = components

    def clone(self, cls=None, clone=None):
        if cls is None:
            cls = type(self)

        price = cls(
            self.amount,
            currency=self.currency,
            component=self.component
        )
        price.components = self.components.copy()
        return price

    def round(self, digits=2):
        price = self.clone()
        price.amount = safe_decimal(Decimal(str(round(price.amount, digits))))
        price.components = {
            component:
                safe_decimal(Decimal(str(round(amount, digits))))
            for component, amount
            in six.iteritems(price.components)
        }
        return price

    def __add__(self, other):
        self.sanity_check(other)
        price = self.clone()
        price.amount = safe_decimal(price.amount + other.amount)
        price.components = merge_amount_dicts(
            price.components,
            other.components,
            lambda a, b: safe_decimal(a + b)
        )
        return price

    def __sub__(self, other):
        self.sanity_check(other)
        price = self.clone()
        price.amount = safe_decimal(price.amount - other.amount)
        price.components = merge_amount_dicts(
            price.components,
            other.components,
            lambda a, b: safe_decimal(a - b)
        )
        return price

    def __mul__(self, multiplier):
        price = self.clone()
        price.amount = safe_decimal(price.amount * multiplier)
        price.components = {
            component: safe_decimal(amount * multiplier)
            for component, amount in six.iteritems(price.components)
        }
        return price

    def __rmul__(self, multiplier):
        return self.__mul__(multiplier)

    def __div__(self, divider):
        price = self.clone()
        price.amount /= divider
        price.components = {
            component: safe_decimal(amount / divider)
            for component, amount in six.iteritems(price.components)
        }
        return price

    def __rdiv__(self, divider):
        return self.__div__(divider)

    def __neg__(self):
        price = self.clone()
        price.amount = -price.amount
        price.components = {
            component: safe_decimal(-amount)
            for component, amount in six.iteritems(price.components)
        }
        return price

    def __eq__(self, other):
        if not isinstance(other, Price):
            return NotImplemented

        return (
            self.currency == other.currency and self.amount == other.amount and
            self.component == other.component and
            self.components == other.components
        )

    def __ne__(self, other):
        if not isinstance(other, Price):
            return NotImplemented

        return (
            self.currency != other.currency or self.amount != other.amount or
            self.component != other.component or
            self.components != other.components
        )

    def __hash__(self):
        return hash(
            (
                self.currency, self.amount, self.component, frozenset(
                    self.components.items()
                )
            )
        )

    def __contains__(self, component):
        if not isinstance(component, (basestring, PriceComponent)):
            raise TypeError()
        elif isinstance(component, PriceComponent):
            return bool(component.extract_price(self))
        return component in self.components

    def __getitem__(self, component):
        if component in self.components:
            return Price(
                self.components[component],
                currency=self.currency,
                component=component
            )
        elif isinstance(component, PriceComponent):
            return component.extract_price(self)
        raise KeyError(component)

    def __setitem__(self, component, value):
        amount = value
        if isinstance(amount, Price):
            amount = value.amount
        self.components[component] = safe_decimal(amount)

    def __len__(self):
        return len(self.components)

    def __iter__(self):
        for component, amount in six.iteritems(self.components):
            yield (
                component, Price(
                    amount,
                    currency=self.currency,
                    component=component
                )
            )

    def __nonzero__(self):
        return self.amount != 0

    def __unicode__(self):
        return self.currency.format(self.amount)

    def __repr__(self):
        return str(self.amount)
