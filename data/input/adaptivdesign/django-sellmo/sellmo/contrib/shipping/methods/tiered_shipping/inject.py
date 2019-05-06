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

from django.core.exceptions import ValidationError
from django.utils.module_loading import import_string

from sellmo.conf import get_setting
from sellmo.core.loading import load

from .constants import MAX_TIER_ATTRIBUTES

import sellmo.contrib.settings as _settings


def _attribute_types(value):
    types = {}
    for typ in value:
        if isinstance(typ, basestring):
            typ = import_string(typ)()
        types[typ.key] = typ
    return types


@load(before='finalize_settings_SiteSettings')
def load_model():

    if MAX_TIER_ATTRIBUTES == 0:
        return

    tiered_attribute_types = _attribute_types(
        get_setting(
            'TIERED_ATTRIBUTE_TYPES',
            default=[
                'sellmo.contrib.attribute.types.IntegerAttributeType',
                'sellmo.contrib.attribute.types.FloatAttributeType',
            ]
        )
    )

    class SiteSettings(_settings.models.SiteSettings):
        def clean(self):

            errors = {}
            for i in range(MAX_TIER_ATTRIBUTES):
                attr = 'shipping_tier_attribute{0}'.format(i + 1)
                attribute = getattr(self, attr, None)
                if attribute is None:
                    continue

                attribute_type = type(attribute.get_type())
                if (
                    not any(
                        [
                            issubclass(attribute_type,
                                       typ) for typ in tiered_attribute_types
                        ]
                    )
                ):

                    errors[attr] = [
                        _("Invalid attribute type, must be numeric.")
                    ]

            if errors:
                raise ValidationError(errors)

        class Meta(_settings.models.SiteSettings.Meta):
            abstract = True

    _settings.models.SiteSettings = SiteSettings
