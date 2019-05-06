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
from django.utils.text import capfirst
from django.utils.translation import ugettext_lazy as _

from .descriptors import VariantFieldDescriptor
from .helpers import differs_field_name


class BaseVariant(models.Model):

    exclude_product_fields = ['content_type', 'slug', 'product']
    exclude_field_types = [models.BooleanField, models.ManyToManyField]

    @classmethod
    def setup(cls, base_cls):
        cls.__base_cls__ = base_cls
        for field in cls.get_variable_fields(base_cls):
            descriptor = field.model.__dict__.get(field.name, None)
            setattr(
                cls,
                field.name,
                VariantFieldDescriptor(
                    field,
                    descriptor=descriptor
                )
            )
            cls.add_to_class(
                differs_field_name(field.name),
                models.BooleanField(
                    editable=False,
                    auto_created=True,
                    default=False
                )
            )

    @classmethod
    def get_variable_fields(cls, base_cls):
        fields = []
        for field in cls._meta.get_fields():
            if (
                not field.auto_created and
                not field.name in cls.exclude_product_fields and
                not isinstance(field, tuple(cls.exclude_field_types)) and
                not field in base_cls._meta.get_fields()
            ):
                fields.append(field)
        return fields

    def save(self, *args, **kwargs):

        if hasattr(self, 'product_id') and self.product_id is not None:
            product = self.product
        else:
            raise Exception("Variant cannot be saved without a parent product")

        # See if object is newly created
        exists = self.pk is None

        def assign_field(field, val, product_val):
            differs = getattr(self, differs_field_name(field.name))

            if not val:
                # Empty field will always copy it's parent field.
                val = product_val
                differs = False
            elif not exists and val != product_val:
                # Descriptor won't work for newly created variants.
                # Set differs to True manually
                differs = True
            elif not differs and val != product_val:
                # Parent has changed, copy field value.
                val = product_val
            elif differs and val == product_val:
                # We don't differ anymore
                differs = False

            setattr(self, field.name, val)
            setattr(self, differs_field_name(field.name), differs)

        # Copy fields
        for field in self.get_variable_fields(self.__base_cls__):
            val = getattr(self, field.name)
            product_val = getattr(product, field.name)
            assign_field(field, val, product_val)

        super(BaseVariant, self).save(*args, **kwargs)

    class Meta:
        abstract = True
