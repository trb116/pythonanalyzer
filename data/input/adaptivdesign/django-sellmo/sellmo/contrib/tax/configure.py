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

from django.db.models.signals import post_save, pre_delete, m2m_changed
from django.db import models
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from sellmo import params
from sellmo.core import indexing
from sellmo.apps.pricing import Price
from sellmo.apps.customer.constants import ADDRESS_TYPES
from sellmo.utils.text import underscore_concat

from sellmo.contrib.settings import settings_manager
from sellmo.contrib.settings.signals import setting_changed

from .models import Tax, TaxRule, ProductTaxClass
from .constants import (
    TAX, DISPLAY_PRICES_INCLUDING_TAX, DISPLAY_PRICES_EXCLUDING_TAX,
    DISPLAY_PRICES_INCLUDING_EXCLUDING_TAX, POLICY_CUSTOMER_ADDRESS
)

group = _("Taxes")

POLICY_CHOICES = tuple(
    (
        underscore_concat(POLICY_CUSTOMER_ADDRESS, address_type),
        _("%s address") % address_type
    ) for address_type in ADDRESS_TYPES
)

POLICY_DEFAULT = POLICY_CHOICES[0][0] if POLICY_CHOICES else None

settings_manager.add_setting(
    'tax_policy',
    models.CharField(
        max_length=80,
        null=POLICY_DEFAULT is None,
        blank=POLICY_DEFAULT is None,
        default=POLICY_DEFAULT,
        choices=POLICY_CHOICES,
        verbose_name=_("tax policy"),
    ),
    group
)

settings_manager.add_setting(
    'tax_inclusive',
    models.BooleanField(
        default=False,
        verbose_name=_("tax inclusive"),
    ),
    group
)

settings_manager.add_setting(
    'tax_breakdown',
    models.BooleanField(
        default=False,
        verbose_name=_("tax breakdown"),
    ),
    group
)

DISPLAY_PRICES_CHOICES = (
    (DISPLAY_PRICES_INCLUDING_TAX, _("including tax")),
    (DISPLAY_PRICES_EXCLUDING_TAX, _("excluding tax")),
    (DISPLAY_PRICES_INCLUDING_EXCLUDING_TAX, _("including & excluding tax")),
)

settings_manager.add_setting(
    'tax_display_prices',
    models.CharField(
        max_length=30,
        default=DISPLAY_PRICES_INCLUDING_TAX,
        choices=DISPLAY_PRICES_CHOICES,
        verbose_name=_("display prices"),
    ),
    group
)


def on_setting_changed(sender, setting, old, new, site, **kwargs):
    if setting in ('tax_inclusive', ):
        index = indexing.indexer.get_index('product')
        index.sync()


setting_changed.connect(on_setting_changed)


def on_tax_class_m2m_changed(sender, instance, action, reverse, **kwargs):
    if params.loaddata:
        return

    if action in ('pre_clear', 'pre_remove', 'post_add'):
        if not reverse:
            _update_indexes(tax_class=instance)
        else:
            index = indexing.indexer.get_index('product')
            index.sync([instance.pk])


def on_tax_class_pre_delete(sender, instance, **kwargs):
    _update_indexes(tax_class=instance)


def on_tax_class_post_save(sender, instance, raw=False, **kwargs):
    if raw:
        return
    _update_indexes(tax_class=instance)


def on_tax_rule_m2m_changed(sender, instance, action, reverse, **kwargs):
    if params.loaddata:
        return
    if action.startswith('post_'):
        _update_indexes(tax_rule=instance)


def on_tax_rule_pre_delete(sender, instance, **kwargs):
    _update_indexes(tax_rule=instance)


def on_tax_rule_post_save(sender, instance, raw=False, **kwargs):
    if raw:
        return
    _update_indexes(tax_rule=instance)


def on_tax_pre_delete(sender, instance, **kwargs):
    _update_indexes(tax=instance)


def on_tax_post_save(sender, instance, raw=False, **kwargs):
    if raw:
        return
    _update_indexes(tax=instance)


def _update_indexes(tax_class=None, tax_rule=None, tax=None):
    products = None
    index = indexing.indexer.get_index('product')
    index.sync(products)


for relation in ProductTaxClass.M2M_INVALIDATIONS:
    field = getattr(ProductTaxClass, relation)
    m2m_changed.connect(on_tax_class_m2m_changed, sender=field.through)

post_save.connect(on_tax_class_post_save, sender=ProductTaxClass)
pre_delete.connect(on_tax_class_pre_delete, sender=ProductTaxClass)

m2m_changed.connect(on_tax_rule_m2m_changed,
                    sender=TaxRule.product_classes.through)
m2m_changed.connect(on_tax_rule_m2m_changed,
                    sender=TaxRule.customer_groups.through)
m2m_changed.connect(on_tax_rule_m2m_changed, sender=TaxRule.taxes.through)
post_save.connect(on_tax_rule_post_save, sender=TaxRule)
pre_delete.connect(on_tax_rule_pre_delete, sender=TaxRule)

for subtype in Tax.SUBTYPES:
    post_save.connect(on_tax_post_save, sender=subtype)
    pre_delete.connect(on_tax_pre_delete, sender=subtype)
