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

from django.utils.translation import ugettext_lazy as _, string_concat

from sellmo.apps.pricing import Price

from .models import Shipment
from .routines import get_shipping_methods


class ShippingMethod(object):
    def __init__(self, identifier, name, carrier=None):
        self.identifier = identifier
        self.name = name
        self.carrier = carrier

    @property
    def string(self, value):
        if self.carrier is not None:
            return '|'.join([self.identifier, self.carrier.identifer])
        return self.identifer

    @staticmethod
    def parse(string, methods):
        method = ({method: method for method in methods}.get(string, None))

        if method is None:
            raise ValueError(string)

        return method

    @staticmethod
    def from_shipment(shipment):
        method = shipment.reconstruct_method()

        if method is NotImplemented:
            method = self.parse(string, get_shippings_methods(shipment.order))

        return method

    @property
    def display(self):
        if self.carrier is not None:
            return _(u"{method} by {carrier}").format(
                method=self.name,
                carrier=self.carrier
            )
        return self.name

    @property
    def choice_display(self):
        costs = self.get_costs()
        if costs:
            return string_concat(
                _(u"+{costs} ".format(costs=costs)),
                self.display)
        return self.display

    def get_base_costs(self, order):
        return Price(0)

    def get_costs(self, order):
        costs = self.get_base_costs()
        if self.carrier is not None:
            costs += self.carrier.extra_costs
        return costs

    def new_shipment(self, order):
        return Shipment()

    def make_shipment(self, order):
        if not self.is_available(order):
            raise ValueError(order)
        shipment = self.new_shipment(order)
        shipment.order = order
        shipment.costs = self.get_costs(order)
        shipment.method_string = self.string
        shipment.description = unicode(self)
        return shipment

    def is_available(self, order):
        return True

    def process(self, request, order, next_step=None):
        return next_step

    def __eq__(self, other):
        if not isinstance(other, ShippingMethod):
            return NotImplemented
        return self.string == other.string

    def __hash__(self):
        return self.string

    def __unicode__(self):
        return self.display
