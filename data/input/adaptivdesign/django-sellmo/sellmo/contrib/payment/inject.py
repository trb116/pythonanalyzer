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

from sellmo.core.loading import load

NO_MUTATION = object()

import sellmo.apps.checkout as _checkout


@load(before='finalize_checkout_Order')
def load_model():
    class Order(_checkout.models.Order):

        _mutated_payment = NO_MUTATION

        def invalidate(self):
            super(Order, self).invalidate()
            self.payment_method = None

        @property
        def payment(self):
            if self._mutated_payment is not NO_MUTATION:
                return self._mutated_payment
            return getattr(self, 'order_payment', None)

        def get_payment_method(self):
            if self.payment is not None:
                from .method import PaymentMethod
                return PaymentMethod.from_payment(self.payment)

        def set_payment_method(self, value):
            payment = None
            if value is not None:
                payment = value.make_payment(self)
            self._mutated_payment = payment

        payment_method = property(get_payment_method, set_payment_method)

        def save(self, *args, **kwargs):

            super(Order, self).save(*args, **kwargs)

            # Save payment
            if self._mutated_payment is not NO_MUTATION:
                if hasattr(self, 'order_payment'):
                    self.order_payment.delete()
                    # Clear the relation cache
                    self.order_payment.order = None
                if self._mutated_payment is not None:
                    self._mutated_payment.order = self
                    self._mutated_payment.save()
                self._mutated_payment = NO_MUTATION

        class Meta(_checkout.models.Order.Meta):
            abstract = True

    _checkout.models.Order = Order
