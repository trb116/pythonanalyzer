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
from django.db.models.query import ValuesQuerySet
from django.utils import six
from django.utils.translation import ugettext_lazy as _

from sellmo.utils.query import PKIterator
from sellmo.utils.text import call_or_format

from mptt.models import MPTTModel, TreeForeignKey, TreeManager
from mptt.querysets import TreeQuerySet

import polymorphism

from ..fields import AttributeKeyField, AttributeTypeField
from ..constants import VALUE_FORMAT
from ..types import types as attribute_types

import sellmo.contrib.attribute as _attribute
import sellmo.apps.product as _product


class SmartValueValuesQuerySet(ValuesQuerySet):

    def smart_sort(self, attribute=None, product=None):
        return self.all()

    def iterator(self):
        rows = []

        def get_used_value_type(row, last_col=None):
            if last_col:
                typ = value_types.get(last_col, None)
                if typ and not typ.is_empty(row[last_col]):
                    return typ, last_col
            for col in row:
                typ = value_types.get(col, None)
                if typ and not typ.is_empty(row[col]):
                    # Keep track of last col to speed
                    # up large querysets
                    return typ, col
            return None, None

        value_types = {
            typ.get_value_field_name(): typ
            for typ in six.itervalues(attribute_types)
        }

        # Keeps track of pk's for each model to prefetch
        value_models = {
            typ.get_model(): set()
            for typ in six.itervalues(attribute_types) if typ.get_model()
        }

        # Keeps track of pk's for attribute to prefetch
        attributes = set()
        last_col = None

        for row in super(SmartValueValuesQuerySet, self).iterator():
            if 'attribute' in row:
                attributes.add(row['attribute'])

            typ, last_col = get_used_value_type(row, last_col)
            if typ:
                value = row[typ.get_value_field_name()]
                row['value'] = value
                model = typ.get_model()
                if model:
                    value_models[model].add(value)
            else:
                row['value'] = None

            rows.append(row)

        # Lookup Attributes
        attributes = (
            {
                obj.pk: obj
                for obj in PKIterator(
                    _attribute.models.Attribute, attributes
                )
            } if attributes else {}
        )

        # Lookup value models
        value_models = {
            model: (
                {
                    obj.pk: obj
                    for obj in PKIterator(model, pks)
                } if pks else {}
            )
            for model, pks in six.iteritems(value_models)
        }

        for row in rows:
            if 'attribute' in row:
                row['attribute'] = attributes[row['attribute']]
            typ, last_col = get_used_value_type(row, last_col)
            if typ:
                model = typ.get_model()
                if model:
                    row['value'] = value_models[model][row['value']]
            yield row


class ValueQuerySet(polymorphism.PolymorphicRelatedQuerySet):
    def for_product(self, product):
        return self.filter(product=product)

    def for_attribute(self, attribute):
        return self.filter(attribute=attribute)

    def smart_values(self, *fields):
        fields = list(fields)
        value_field_names = [
            typ.get_value_field_name()
            for typ in six.itervalues(attribute_types)
        ]

        if 'value' in fields:
            fields.remove('value')
            fields.extend(value_field_names)

        values = self.values(*fields)
        values = values._clone(klass=SmartValueValuesQuerySet)
        return values.order_by(*fields)


class ValueManager(models.Manager):
    def get_by_natural_key(self, attribute, product, value, queryset=None):

        attribute = _attribute.models.Attribute.objects.get_by_natural_key(
            *attribute
        )

        if queryset is None:
            queryset = self.all()

        queryset = queryset.filter(
            attribute=attribute,
            product=_product.models.Product.objects.get_by_natural_key(
                *product)
        )
        return attribute.get_type().get_value_by_natural_key(queryset, *value)


class Value(models.Model):

    # E(A)V
    attribute = models.ForeignKey(
        'attribute.Attribute',
        db_index=True,
        verbose_name=_(u"attribute"),
        related_name='values',
        on_delete=models.PROTECT
    )

    # (E)AV
    product = models.ForeignKey(
        'product.Product',
        db_index=True,
        related_name='values',
    )

    def get_value(self):
        field_name = self.attribute.get_type().get_value_field_name()
        value = getattr(self, field_name)
        return self.attribute.get_type().from_db_value(value)

    def set_value(self, value):
        value = self.attribute.get_type().prep_db_value(value)
        if value != self.get_value():
            self._old_value = self.get_value()
        field_name = self.attribute.get_type().get_value_field_name()
        setattr(self, field_name, value)

    value = property(get_value, set_value)

    _old_value = None

    def get_old_value(self):
        if self._old_value is None:
            return self.get_value()
        return self._old_value

    old_value = property(get_old_value)

    def is_empty(self):
        return self.attribute.get_type().is_empty(self.get_value())

    def save_or_delete_value(self):
        if not self.is_empty():
            self.save()
        elif not self.pk is None:
            self.delete()

    def natural_key(self):
        return (
            self.attribute.natural_key(), self.product.natural_key(),
            self.attribute.get_type().value_natural_key(self.get_value())
        )

    natural_key.dependencies = ['attribute.attribute', 'product.product']

    def __unicode__(self):
        # Do not simply supply value=self, this would encourage recursive calls to
        # __unicode__
        return call_or_format(
            VALUE_FORMAT,
            value=self.value,
            attribute=self.attribute
        )

    class Meta:
        abstract = True
        app_label = 'attribute'
        verbose_name = _("value")
        verbose_name_plural = _("values")



class AttributeQuerySet(models.QuerySet):

    def for_attribute_set(self, sett, recurse=True):
        if recurse:
            return self.filter(
                sets__in=sett.get_ancestors(include_self=True)
            )
        else:
            return self.filter(sets__in=[sett])

    def for_product(self, product):
        return self.filter(values__product=product).distinct()


class AttributeManager(models.Manager):
    def get_by_natural_key(self, key):
        return self.get(key=key)


class Attribute(models.Model):

    name = models.CharField(max_length=100)

    key = AttributeKeyField(max_length=50, db_index=True, blank=True)

    required = models.BooleanField(default=False, verbose_name=_("required"), )

    sets = models.ManyToManyField(
        'attribute.AttributeSet',
        blank=True,
        related_name='attributes',
        verbose_name=_("attribute sets")
    )

    visible = models.BooleanField(default=True, verbose_name=_("visible"), )

    indexed = models.BooleanField(default=True, verbose_name=_("indexed"), )

    sort_order = models.SmallIntegerField(
        default=0,
        verbose_name=_("sort order"),
    )

    def save(self, *args, **kwargs):
        old = None

        if self.pk:
            old = _attribute.models.Attribute.objects.get(pk=self.pk)
        elif not self.key:
            self.key = AttributeKeyField.key_from_name(self.name)

        if old is not None and old.values.count() > 0:
            if self.type != old.type:
                raise Exception(
                    (
                        _(
                            "Cannot change attribute type "
                            "of an attribute that is already "
                            " in use."
                        )
                    )
                )

        super(Attribute, self).save(*args, **kwargs)

    def get_type(self):
        return attribute_types[self.type]

    def natural_key(self):
        return (self.key, )

    def __unicode__(self):
        return self.name

    class Meta:
        abstract = True
        app_label = 'attribute'
        ordering = ['sort_order', 'name']
        verbose_name = _("attribute")
        verbose_name_plural = _("attributes")


class AttributeChoiceQuerySet(models.QuerySet):
    pass


class AttributeChoiceManager(models.Manager):
    def get_by_natural_key(self, attribute, value):
        attribute = _attribute.models.Attribute.objects.get_by_natural_key(
            *attribute
        )
        queryset = self.filter(attribute=attribute)
        return attribute.get_type().get_value_by_natural_key(queryset, *value)


class AttributeChoice(models.Model):

    attribute = models.ForeignKey(
        'attribute.Attribute',
        db_index=True,
        verbose_name=_(u"attribute"),
        related_name='choices',
    )

    def get_value(self):
        field_name = self.attribute.get_type().get_value_field_name()
        value = getattr(self, field_name)
        return self.attribute.get_type().from_db_value(value)

    def set_value(self, value):
        value = self.attribute.get_type().prep_db_value(value)
        if value != self.get_value():
            self._old_value = self.get_value()
        field_name = self.attribute.get_type().get_value_field_name()
        setattr(self, field_name, value)

    value = property(get_value, set_value)

    def natural_key(self):
        return (
            self.attribute.natural_key(),
            self.attribute.get_type().value_natural_key(self.get_value())
        )

    natural_key.dependencies = ['attribute.attribute']

    def __unicode__(self):
        return unicode(self.value)

    class Meta:
        abstract = True
        app_label = 'attribute'
        verbose_name = _("Attribute choice")
        verbose_name_plural = _("Attribute choices")


class AttributeSetQuerySet(TreeQuerySet):
    def in_parent(self, sett, recurse=True):
        q = self.filter(tree_id=sett.tree_id)
        if recurse:
            return q.filter(level__gt=sett.level)
        else:
            return q.filter(level=sett.level + 1)

    def flat_ordered(self):
        return self.order_by('tree_id', 'lft')


class AttributeSetManager(TreeManager):
    def get_by_natural_key(self, full_name):
        parts = full_name.split('/')
        sett = None
        for name in parts:
            sett = self.get(parent=sett, name=name)
        return sett


class AttributeSet(MPTTModel):

    sort_order = models.SmallIntegerField(
        default=0,
        verbose_name=_("sort order"),
    )

    parent = TreeForeignKey(
        'self',
        blank=True,
        null=True,
        verbose_name=_("parent set"),
        related_name='children'
    )

    name = models.CharField(max_length=255, verbose_name=_("name"), )

    def get_nodes(self, ancestors=None):
        if ancestors is None:
            ancestors = self.get_ancestors(include_self=True)
        else:
            ancestors = ancestors + [self]
        return ancestors

    nodes = property(get_nodes)

    def get_full_name(self, ancestors=None):
        return " | ".join(sett.name for sett in self.get_nodes(ancestors))

    full_name = property(get_full_name)

    def natural_key(self):
        return ('/'.join(sett.name for sett in self.get_nodes()), )

    def __unicode__(self):
        return self.full_name

    class MPTTMeta:
        order_insertion_by = ['sort_order', 'name']

    class Meta:
        abstract = True
        app_label = 'attribute'
        verbose_name = _("Attribute set")
        verbose_name_plural = _("Attribute sets")
