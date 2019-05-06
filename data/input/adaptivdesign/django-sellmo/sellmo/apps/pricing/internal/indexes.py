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

from sellmo.core import indexing
from sellmo.utils.text import underscore_concat

from django.utils import six

from ..price import Price
from ..currency import Currency
from ..exceptions import CurrencyNotAvailable
from ..constants import DECIMAL_PLACES, DECIMAL_MAX_DIGITS
from ..helpers import price_field_name, price_field_names


class PriceSearchQuerySet(indexing.SearchQuerySet):
    def order_by_price(self, prefix, currency=None):
        field_name = price_field_name(prefix, currency=currency)
        return self.order_by(field_name)

    def with_price_field(self, prefix, currency=None):
        field_names = price_field_names(
            prefix,
            multi_currency=True,
            currencies=[currency],
            components=True,
            extra_fields=True
        )
        return self.with_fields(*field_names)

    def can_use_price_field(self, prefix, currency=None):
        field_names = price_field_names(
            prefix,
            multi_currency=True,
            currencies=[currency],
            components=True,
            extra_fields=True
        )
        return all(
            self.can_use_field(field_name) for field_name in field_names
        )


class PriceIndex(indexing.Index):

    price_prefixes = []

    def populate(self, document, values, **variety):
        values = super(PriceIndex, self).populate(document, values, **variety)
        kwargs = self.get_price_kwargs(document, **variety)

        for prefix in self.price_prefixes:
            for currency in Currency.get_all():
                try:
                    price = self.get_price(
                        document, prefix, currency, **kwargs
                    )
                except CurrencyNotAvailable:
                    price = None

                if price is None:
                    continue

                field_name = price_field_name(prefix, currency=currency)
                values[field_name] = price.amount

                for component in Price.COMPONENTS:
                    multiplicity = 0
                    for (
                        amount, extra_values
                    ) in component.safe_extract(price):
                        multiplicity += 1

                        field_name = price_field_name(
                            prefix,
                            currency=currency,
                            component=component,
                            multiplicity=multiplicity
                        )
                        amount, extra_values = component.prepare_for_index(
                            amount, extra_values
                        )

                        values[field_name] = amount
                        for extra_field_name in component.extra_fields:
                            full_extra_field_name = underscore_concat(
                                field_name, extra_field_name
                            )
                            values[full_extra_field_name] = extra_values.get(
                                extra_field_name
                            )

        return values

    def get_price_kwargs(self, document, **variety):
        return {}

    def get_price(self, document, prefix, currency=None, **kwargs):
        raise NotImplementedError()

    def has_indexed_price(self, document, prefix, currency=None):
        values = getattr(document, '_index_values', {})
        field_name = price_field_name(prefix, currency=currency)
        return field_name in values

    def get_indexed_price(self, document, prefix, currency=None):
        values = getattr(document, '_index_values', {})
        field_name = price_field_name(prefix, currency=currency)

        if field_name not in values:
            raise Exception("%s not found in index" % field_name)

        amount = values.get(field_name)

        if amount is None:
            return None

        price = Price(amount, currency=currency)

        for component in Price.COMPONENTS:
            field_names = price_field_names(
                prefix,
                multi_currency=True,
                currencies=[currency],
                components=[component],
                components_only=True
            )
            for field_name in field_names:
                if field_name not in values:
                    raise Exception("%s not found in index" % field_name)
                amount = values[field_name]
                if amount is None:
                    # Due to multiplicity, we can have unused fields.
                    # Do not apply these.
                    continue
                extra_values = {}

                for extra_field_name in component.extra_fields:
                    full_extra_field_name = underscore_concat(
                        field_name, extra_field_name
                    )
                    if full_extra_field_name not in values:
                        raise Exception(
                            "%s not found in index" % full_extra_field_name
                        )
                    extra_values[
                        extra_field_name
                    ] = values[full_extra_field_name]

                amount, extra_values = component.prepare_from_index(
                    amount, extra_values
                )
                price = component.apply(price, amount, extra_values)

        return price

    def get_fields(self):
        fields = super(PriceIndex, self).get_fields()

        for prefix in self.price_prefixes:
            for currency in Currency.get_all():

                field_name = price_field_name(prefix, currency=currency)
                fields[field_name] = indexing.DecimalField(
                    max_digits=DECIMAL_MAX_DIGITS,
                    decimal_places=DECIMAL_PLACES
                )

                for component in Price.COMPONENTS:
                    field_names = price_field_names(
                        prefix,
                        multi_currency=True,
                        currencies=[currency],
                        components=[component],
                        components_only=True
                    )
                    for field_name in field_names:
                        fields[field_name] = indexing.DecimalField(
                            max_digits=DECIMAL_MAX_DIGITS,
                            decimal_places=DECIMAL_PLACES
                        )

                        for extra_field_name, extra_field in six.iteritems(
                            component.construct_extra_index_fields()
                        ):
                            full_extra_field_name = underscore_concat(
                                field_name, extra_field_name
                            )
                            fields[full_extra_field_name] = extra_field

        return fields
