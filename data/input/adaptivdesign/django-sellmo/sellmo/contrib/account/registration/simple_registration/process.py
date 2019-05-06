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

from django.utils import six
from django.core.exceptions import ValidationError

from sellmo.utils.text import underscore_concat
from sellmo.contrib.account.forms import UserCreationForm # NOQA

from sellmo.contrib.account.registration.process import ( # NOQA
    AbstractRegistrationProcess, AbstractRegistrationStep
)

from sellmo.apps.customer.forms import CustomerForm, AddressForm # NOQA
from sellmo.apps.customer.constants import ADDRESS_TYPES

from .views import information_step


class SimpleRegistrationProcess(AbstractRegistrationProcess):
    def get_first_step(self):
        return InformationStep(self.request, self.customer)


class InformationStep(AbstractRegistrationStep):

    key = 'information'
    invalid_context = None

    def is_completed(self):
        try:
            self.customer.full_clean(exclude=['user'])
            if getattr(self.customer, 'user', None) is None:
                return False
            self.customer.user.full_clean()
        except ValidationError:
            return False
        return True

    def contextualize_or_complete(self, request, context, data=None):

        completed = True
        customer = self.customer
        user = customer.user
        user_form = None

        if user.pk is None:
            # No prefixing here, in order to utilize overlapping fields
            user_form = UserCreationForm(data, instance=user)

            completed &= data and user_form.is_valid()
            if completed:
                user = user_form.save(commit=False)
            context['user_form'] = user_form

        # No prefixing here, in order to utilize overlapping fields
        customer_form = CustomerForm(data, instance=customer)

        completed &= data and customer_form.is_valid()
        if completed:
            customer = customer_form.save(commit=False)
        context['customer_form'] = customer_form

        # We are overlapping customer form fields with user form fields.
        # This will most likely only be the 'email' field. Since additional
        # validation happens by the user form, we need to copy over
        # these errors to the customer form.
        if user_form is not None:
            for field, error in six.iteritems(user_form.errors.as_data()):
                if field in customer_form.fields:
                    customer_form.add_error(field, error)

        addresses = {}
        for address_type in ADDRESS_TYPES:
            form = AddressForm(
                data,
                prefix=underscore_concat(address_type, 'address'),
                instance=customer.addresses.get(address_type, None),
            )

            completed &= data and form.is_valid()
            if completed:
                address = form.save(commit=False)
                addresses[address_type] = address
            context[underscore_concat(address_type, 'address_form')] = form

        if completed:
            for address_type in ADDRESS_TYPES:
                address = addresses[address_type]
                customer.addresses[address_type] = address

            customer.user = user

        return completed

    def complete(self, data):
        self.invalid_context = {}
        return self.contextualize_or_complete(
            self.request, self.invalid_context, data
        )

    def render(self, request, context):
        if self.invalid_context is None:
            self.contextualize_or_complete(request, context)
        else:
            context.update(self.invalid_context)

        return information_step(request, self.customer, context)
