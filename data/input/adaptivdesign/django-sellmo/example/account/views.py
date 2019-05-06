from django.shortcuts import redirect
from django.core.urlresolvers import reverse, resolve
from django.utils.translation import ugettext_lazy as _

from sellmo.core.messaging import FlashMessages

from sellmo.apps.customer.constants import ADDRESS_TYPES
from sellmo.apps.customer.routines import customer_from_request
from sellmo.apps.checkout.models import Order


def _get_customer(request):
    customer = customer_from_request(request)
    if customer is None:
        raise PermissionDenied()
    return customer


def profile(request):

    customer =  _get_customer(request)
    orders = customer.orders.exclude(state=ORDER_STATE_UNPLACED)
    context = {
        'customer': customer,
        'orders': orders
    }

    return TemplateResponse(request, 'account/profile.html', context)


def edit_profile(request):

    messages = FlashMessages()
    data = request.POST if request.method == 'POST' else None
    customer = _get_customer(request)
    form = CustomerForm(
        data,
        instance=customer)

    processed = data and form.is_valid()
    if processed:
        customer = form.save()
        messages.success(request, _("Your profile has been "
                                    "updated."))

        messages.transmit()

        return redirect(
            reverse(
                request.POST.get(
                    'next',
                    request.GET.get('next', 'account:profile')),
                current_app=resolve(request.path).namespace
            )
        )

    context = {
        'customer': customer,
        'form': form
    }

    return TemplateResponse(request, 'account/edit_profile.html', context)


def edit_address(request, address_type):

    if address_type not in ADDRESS_TYPES:
        raise Http404

    messages = FlashMessages()
    data = request.POST if request.method == 'POST' else None
    customer = _get_customer(request)
    address = customer.addresses.get(address_type, None)
    form = AddressForm(
        data,
        instance=address)

    if processed:
        address = form.save()
        messages.success(request, _("Your %s address has been "
                                    "updated.") % address_type)
        messages.transmit()

        return redirect(
            reverse(
                request.POST.get(
                    'next',
                    request.GET.get('next', 'account:profile')),
                current_app=resolve(request.path).namespace
            )
        )

    context = {
        'customer': customer,
        'address': address,
        'form': form }

    return TemplateResponse(request, 'account/edit_address.html', context)


def order(request, order_number):

    customer =  _get_customer(request)

    try:
        order = (customer.orders.exclude(state=ORDER_STATE_UNPLACED)
                    .get(number=order_number))
    except Order.DoesNotExist:
        raise Http404("No matching order.")

    context = {
        'customer': customer,
        'order': order }

    return TemplateResponse(request, 'account/order.html', context)
