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

from django.core.exceptions import ObjectDoesNotExist

from sellmo.apps.checkout.process import AbstractCheckoutStep # NOQA
from sellmo.apps.customer.routines import customer_from_request
from sellmo.contrib.account.forms import AuthenticationForm # NOQA
from sellmo.contrib.account.routines import login_user

from .views import login_step


class CheckoutLoginStep(AbstractCheckoutStep):

    _context = None
    key = 'login'

    def __init__(self, request, order, next_step):
        super(CheckoutLoginStep, self).__init__(request, order)
        self.next_step = next_step

    def get_next_step(self):
        return self.next_step

    def is_completed(self):
        customer = customer_from_request(self.request)
        return (
            self.order.pk is not None or customer is not None and
            customer.is_authenticated()
        )

    def can_skip(self):
        return True

    def contextualize_or_complete(self, request, context, data=None):

        completed = True

        form = AuthenticationForm(data)
        completed &= data and form.is_valid()
        if completed:
            user = form.get_user()

        # Make sure this user is a customer
        try:
            user.customer is not None
        except ObjectDoesNotExist:
            completed = False

        if completed:
            login_user(request, user)

        return completed

    def complete(self, data):
        self._context = {}
        return self.contextualize_or_complete(self.request, self._context,
                                              data)

    def render(self, request, context):
        if self._context is not None:
            context.update(self.invalid_context)
        else:
            self.contextualize_or_complete(request, context)

        return login_step(request, self.order, context=context)
