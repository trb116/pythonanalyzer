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

from smtplib import SMTPException

from sellmo.contrib.mailing.handlers import AbstractMailHandler
from sellmo.contrib.mailing.signals import mail_send, mail_failed

from django.core import mail


class DefaultMailHandler(AbstractMailHandler):
    def handle_mail(
        self,
        message_type,
        message_reference,
        context,
        connection=None
    ):

        # Open the writer and close it afterwards
        with self.writer.open(context) as writer:

            # See if this writer supports both html and text
            if set(['html', 'text']) == set(writer.formats):
                message = mail.EmailMultiAlternatives()
                message.body = writer.get_body('text')
                message.attach_alternative(
                    writer.get_body('html'), 'text/html'
                )
            else:
                message = mail.EmailMessage()
                if 'html' in writer.formats:
                    message.content_subtype = 'html'
                    message.body = writer.get_body('html')
                elif 'text' in writer.formats:
                    message.body = writer.get_body('text')
                else:
                    raise Exception(
                        "Invalid email formats '{0}'.".format(writer.formats)
                    )

            # Further construct the message
            message.subject = writer.get_subject()
            message.from_email = writer.get_from()

            # Make sure to is a list
            to = writer.get_to()
            if to and not isinstance(to, (list, tuple)):
                to = [to]
            message.to = to

            # Make sure bcc is a list
            bcc = writer.get_bcc()
            if bcc and not isinstance(bcc, (list, tuple)):
                bcc = [bcc]
            message.bcc = bcc

            message.bcc = writer.get_bcc()
            message.header = writer.get_headers()
            message.attachments = writer.get_attachments()

            # If a connection is passed, assign it
            if connection:
                message.connection = connection

            # Now actualy send
            try:
                message.send()
            except SMTPException as exception:
                mail_failed.send(
                    sender=self,
                    message_type=message_type,
                    message_reference=message_reference,
                    context=context,
                    reason=str(exception),
                    message=message,
                )
            else:
                mail_send.send(
                    sender=self,
                    message_type=message_type,
                    message_reference=message_reference,
                    context=context,
                    message=message
                )
