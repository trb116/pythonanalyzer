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

import sellmo.contrib.checkout.mailing as _checkout_mailing


@load(action='finalize_checkout_OrderMailMessage')
def finalize_model():
    class OrderMailMessage(_checkout_mailing.models.OrderMailMessage):

        objects = (
            _checkout_mailing.models.OrderMailMessageManager.from_queryset(
                _checkout_mailing.models.OrderMailMessageQuerySet
            )
        )()

        class Meta(_checkout_mailing.models.OrderMailMessage.Meta):
            app_label = 'checkout'

    _checkout_mailing.models.OrderMailMessage = OrderMailMessage


class OrderMailMessageQuerySet(models.QuerySet):
    pass


class OrderMailMessageManager(models.Manager):
    pass


class OrderMailMessage(models.Model):

    order = models.ForeignKey('checkout.Order')

    mail_message = models.ForeignKey('mailing.MailMessage')

    def __unicode__(self):
        return unicode(self.mail_message)

    class Meta:
        abstract = True
        verbose_name = _("order mail message")
        verbose_name_plural = _("order mail messages")
