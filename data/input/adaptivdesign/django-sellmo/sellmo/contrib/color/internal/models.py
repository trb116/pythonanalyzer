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

from sellmo.core.loading import load

import sellmo.contrib.color as _color


@load(action='finalize_color_Color')
def finalize_model():
    class Color(_color.models.Color):

        objects = _color.models.ColorManager.from_queryset(
            _color.models.ColorQuerySet)()

        class Meta(_color.models.Color.Meta):
            app_label = 'color'

    _color.models.Color = Color


class ColorQuerySet(models.QuerySet):
    pass


class ColorManager(models.Manager):
    def get_by_natural_key(self, name):
        return self.get(name=name)


class Color(models.Model):

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("name")
    )

    value = models.CharField(max_length=6, verbose_name=_("value"))

    def natural_key(self):
        return (self.name, )

    def __unicode__(self):
        return self.name

    class Meta:
        abstract = True
        ordering = ['name']
        verbose_name = _("color")
        verbose_name_plural = _("colors")
