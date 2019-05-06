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

from django.utils.translation import ugettext_lazy as _

from sellmo.conf import get_setting

import pycountry

COUNTRY_CHOICES = [
    (country.alpha2, country.name) for country in list(pycountry.countries)
]

PHONE_NUMBER_ENABLED = get_setting('PHONE_NUMBER_ENABLED', default=True)

PHONE_NUMBER_REQUIRED = get_setting('PHONE_NUMBER_REQUIRED', default=False)

NAME_PREFIX_ENABLED = get_setting('NAME_PREFIX_ENABLED', default=False)

NAME_PREFIX_REQUIRED = get_setting('NAME_PREFIX_REQUIRED', default=True)

NAME_PREFIX_CHOICES = get_setting(
    'NAME_PREFIX_CHOICES',
    default=[
        ('sir', _("sir")),
        ('madame', _("madam")),
    ]
)

NAME_SUFFIX_ENABLED = get_setting('NAME_SUFFIX_ENABLED', default=True)
