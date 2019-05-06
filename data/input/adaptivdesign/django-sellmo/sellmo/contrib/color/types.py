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
from django.utils.translation import ugettext_lazy as _

from sellmo.contrib.attribute.types import AbstactModelAttributeType

import sellmo.contrib.color as _color


class ColorAttributeType(AbstactModelAttributeType):
    @property
    def key(self):
        return 'color'

    @property
    def verbose_name(self):
        return _("color")

    def get_value_field(self):
        return models.ForeignKey, ['color.Color'], {
            'null': True,
            'blank': True,
            'related_name': '+'
        }

    def get_model(self):
        return _color.models.Color

    def value_natural_key(self, value):
        return (self.get_value_field_name(), value.natural_key())

    def get_value_by_natural_key(self, queryset, value_field_name, value):
        return queryset.get(
            **{
                value_field_name:
                self.get_model().objects.get_by_natural_key(*value)
            }
        )

    def parse(self, string):
        try:
            return self.get_model().objects.get(name__iexact=string)
        except self.get_model().DoesNotExist:
            raise ValueError(string)

    def string(self, value):
        return unicode(value.name)
