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

from django.db import transaction
from django.http import Http404
from django.shortcuts import redirect
from django.core.urlresolvers import reverse, resolve

from sellmo.core import chaining
from sellmo.core.exceptions import ViewNotImplemented
from sellmo.core.process.exceptions import ProcessStepNotFound, ProcessError

from .process import CheckoutProcess # NOQA
from .routines import order_from_request, completed_order_from_request


@chaining.define(provides=['order', 'process'])
def checkout(request, step=None, **kwargs):

    order = order_from_request(request)
    if not order:
        raise Http404("Nothing to order.")

    data = request.POST if request.method == 'POST' else None

    process = CheckoutProcess(request, order)

    # If a step is given, attempt to go to the given step
    if step:
        try:
            process.step_to(step)
        except ProcessStepNotFound:
            # If the step can not be found, fall back to
            # the latest step.
            step = None
        except ProcessError as error:
            raise Http404(error)

    # Go to the latest step
    if not step:
        try:
            process.step_to_latest()
        except ProcessError as error:
            raise Http404(error)

        yield redirect(
            reverse(
                'checkout:checkout',
                kwargs={'step': process.current_step.key},
                current_app=resolve(request.path).namespace
            )
        )

    elif data:
        # Perform atomic transactions at this point
        with transaction.atomic():
            success = process.feed(data)
            if order.may_change:
                order.calculate()

            if success:
                # Update order
                order.save()

                # Process step was successfull, redirect to next
                # step
                if not process.is_completed():
                    # Go to the next step
                    yield redirect(
                        reverse(
                            'checkout:checkout',
                            kwargs={'step': process.current_step.key},
                            current_app=resolve(request.path).namespace
                        )
                    )

        # See if we completed the process
        if process.is_completed():
            # Redirect away from this view
            request.session['completed_order'] = order.pk
            yield redirect(
                reverse(
                    'checkout:complete',
                    current_app=resolve(request.path).namespace
                )
            )


    yield chaining.update(
        order=order,
        process=process)

    if (yield chaining.forward).result is None:
        context = {'order': order}
        try:
            result = process.render(request, context=context)
        except ProcessError as error:
            raise Http404(error)

        if result is None:
            raise ViewNotImplemented


@chaining.define(provides=['order'])
def complete(request, order=None, context=None, **kwargs):

    order = completed_order_from_request(request)
    if order is None:
        raise Http404("No order has been checked out.")

    yield chaining.update(order=order)

    result = (yield chaining.forward).result
    if result is None:
        raise ViewNotImplemented
