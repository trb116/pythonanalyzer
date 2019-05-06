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

import logging

from django.db import models
from django.utils.translation import ugettext_lazy as _

from sellmo.apps.checkout.signals import (
    order_paid, order_state_changed, order_status_changed
)

from sellmo.contrib.mailing import mailer
from sellmo.contrib.mailing.signals import mail_send, mail_failed
from sellmo.contrib.mailing.models import MailMessage
from sellmo.contrib.settings import settings_manager

from .constants import ORDER_MAILS
from .models import OrderMailMessage
from .writers import (
    OrderConfirmationMailWriter, OrderNotificationMailWriter,
    ShippingNotificationMailWriter
)

logger = logging.getLogger('sellmo')

mailer.register_writer('order_confirmation', OrderConfirmationMailWriter)
mailer.register_writer('order_notification', OrderNotificationMailWriter)
mailer.register_writer('shipping_notification', ShippingNotificationMailWriter)


def on_mail_send_or_failed(
    sender, message_type, message_reference, context, **kwargs
):

    if message_type in ORDER_MAILS:
        try:
            mail_message = MailMessage.objects.get(
                message_reference=message_reference
            )
        except MailMessage.DoesNotExist:
            logger.warning(
                "Mail message {0} could not be linked to order {1}."
                .format(message_reference, context['order'])
            )
        else:
            OrderMailMessage.objects.create(
                mail_message=mail_message,
                order=context['order'],
            )


mail_send.connect(on_mail_send_or_failed)
mail_failed.connect(on_mail_send_or_failed)


def send_order_mails(order, **event_signature):
    if not settings_manager['send_order_mails']:
        return

    event_signature['instant_payment'] = order.payment.instant
    for message_type, entry in six.iteritems(ORDER_MAILS.find(
        **event_signature)):
        if entry.get('send_once', False):
            send_mails = OrderMailMessage.objects.filter(
                order=order,
                mail_message__message_type=mail,
                mail_message__delivered=True
            )
            if send_mails.count() > 0:
                # Do not send
                continue

        mailer.send_mail(message_type, {'order': order})


def on_order_paid(sender, order, **kwargs):
    send_order_mails(order, {'on_paid': True, })


def on_order_state_changed(sender, order, new_state, old_state=None, **kwargs):
    send_order_mails(
        order, **{
            'state': new_state,
            'on_{0}'.format(new_state): True,
        }
    )


def on_order_status_changed(
    sender,
    order,
    new_status,
    old_status=None,
    **kwargs
):
    send_order_mails(order, {'status': new_status, })


order_paid.connect(on_order_paid)
order_state_changed.connect(on_order_state_changed)
order_status_changed.connect(on_order_status_changed)

group = _("Checkout")

settings_manager.add_setting(
    'send_order_mails',
    models.BooleanField(
        default=True,
        verbose_name=_("send order mails"),
    ),
    group
)
