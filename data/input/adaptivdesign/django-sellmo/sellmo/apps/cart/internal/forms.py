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

from django import forms

from sellmo.apps.purchase.models import Purchase # NOQA


class AddToCartForm(forms.Form):

    qty = forms.IntegerField(min_value=1, initial=1)

    @classmethod
    def factory(cls, data=None, **kwargs):
        return cls

    def get_purchase_args(self):
        return {'qty': self.cleaned_data['qty']}


class EditPurchaseForm(forms.Form):

    @classmethod
    def factory(cls, purchase, data=None, **kwargs):
        Form = type('EditPurchaseForm', (cls,), {
            'purchase': forms.IntegerField(
                initial=purchase.pk,
                widget=forms.HiddenInput
            ),
            'qty': forms.IntegerField(initial=purchase.qty, min_value=0)
        })
        return Form

    def get_edit_purchase_args(self):
        purchase = self.cleaned_data['purchase']
        purchase = Purchase.objects.polymorphic().get(pk=purchase)

        return {'purchase': purchase, 'qty': self.cleaned_data['qty']}
