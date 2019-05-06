from sellmo import modules
from sellmo.core.decorators import link


from django.shortcuts import render


namespace = modules.account.namespace


@chaining.link
def login(request, processed, redirection, context, messages, **kwargs):
    messages.transmit()
    if redirection:
        return redirection
    return render(request, 'account/login.html', context)


@chaining.link
def profile(request, context, **kwargs):
    return render(request, 'account/profile.html', context)


@chaining.link
def order(request, context, **kwargs):
    return render(request, 'account/order.html', context)


@chaining.link
def information_step(request, context, **kwargs):
    shipping = context['shipping_address_form']
    billing = context['billing_address_form']

    same_as_shipping = False
    if not request.method == 'POST':
        same_as_shipping = all(value == billing.initial[key]  for
                               key, value in shipping.initial.iteritems()
                               if not key == 'id')

    if not same_as_shipping and request.POST.get('same_as_shipping', 'no') == 'yes':
        same_as_shipping = True

    context.update({
        'same_as_shipping': same_as_shipping
    })

    return render(request, 'account/registration/information.html', context)
