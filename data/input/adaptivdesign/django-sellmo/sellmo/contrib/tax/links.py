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

from django.db.models import Q

from sellmo.core import chaining
from sellmo.apps.pricing import Price
from sellmo.apps.product.routines import list_products_from_request
from sellmo.apps.customer.models import AddressZone, CustomerGroup
from sellmo.contrib.settings import settings_manager

from .models import ProductTaxClass, Tax, TaxRule
from .constants import (TAX, POLICY_CUSTOMER_ADDRESS_TYPES)


@chaining.link(list_products_from_request, takes_result=True)
def _list_products_from_request(products, request, **kwargs):

    address_type = None
    tax_policy = settings_manager['tax_policy']
    if tax_policy:
        address_type = POLICY_CUSTOMER_ADDRESS_TYPES.get(tax_policy, None)

    default_zone = AddressZone.default(address_type)
    if default_zone is not None and not default_zone.spans(AddressZone.get_current(address_type)):
        products = products.set_bare(True)
        yield products


@chaining.link(Price.calculate, takes_result=True)
def _calculate(
    price,
    product=None,
    shipping_method=None,
    payment_method=None,
    bare=False,
    **kwargs
):

    if bare or price is None or TAX in price:
        return

    tax_policy = settings_manager['tax_policy']
    if tax_policy:
        address_type = POLICY_CUSTOMER_ADDRESS_TYPES.get(tax_policy, None)

    zone = AddressZone.get_current(address_type)
    taxes = Tax.objects.spans(zone)
    tax_rules = TaxRule.objects.none()

    if product:
        product_classes = ProductTaxClass.objects.for_product(product)
        tax_rules = TaxRule.objects.filter(product_classes__in=product_classes)
    elif shipping_method:
        tax_rules = TaxRule.objects.filter(applies_to_shipping_costs=True)
    elif payment_method:
        tax_rules = TaxRule.objects.filter(applies_to_payment_costs=True)

    if 'customer_group' in kwargs:
        customer_group = kwargs['customer_group']
    else:
        CustomerGroup.current_customer_group()

    tax_rules = tax_rules.filter(
        Q(customer_groups=customer_group) | Q(
            customer_groups=None
        )
    )
    taxes = taxes.polymorphic().filter(tax_rules__in=tax_rules).distinct()

    for tax in taxes:
        price = tax.apply(price)

    yield chaining.update(price=price)
    yield price
