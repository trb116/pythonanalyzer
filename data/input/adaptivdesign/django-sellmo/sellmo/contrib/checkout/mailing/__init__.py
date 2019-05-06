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

from sellmo.core.registry import Module
from sellmo.conf import get_setting

from django.utils.functional import cached_property
from django.utils.module_loading import import_string


class WritersModule(Module.imports('%s.internal.writers' % __name__)):
    @cached_property
    def OrderConfirmationMailWriter(self):
        return import_string(
            get_setting(
                'ORDER_CONFIRMATION_MAIL_WRITER',
                default='%s.internal.writers.OrderConfirmationMailWriter' %
                __name__
            )
        )

    @cached_property
    def OrderNotificationMailWriter(self):
        return import_string(
            get_setting(
                'INVOICE_MAIL_WRITER',
                default='%s.internal.writers.OrderNotificationMailWriter' %
                __name__
            )
        )

    @cached_property
    def ShippingNotificationMailWriter(self):
        return import_string(
            get_setting(
                'SHIPPING_NOTIFICATION_MAIL_WRITER',
                default='%s.internal.writers.ShippingNotificationMailWriter' %
                __name__
            )
        )


ModelsModule = Module.imports('%s.internal.models' % __name__)

writers = WritersModule('%s.writers' % __name__)
models = ModelsModule('%s.models' % __name__)

default_app_config = '%s.apps.DefaultConfig' % __name__
