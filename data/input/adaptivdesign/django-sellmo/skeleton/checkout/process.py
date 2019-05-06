from sellmo import modules
from sellmo.contrib.checkout.multistep_checkout.process import MultiStepCheckoutProcess as MultiStepCheckoutProcessBase
from sellmo.contrib.account.checkout.process import CheckoutLoginStep


class MultiStepCheckoutProcess(MultiStepCheckoutProcessBase):
    def get_first_step(self):
        return CheckoutLoginStep(
            request=self.request, order=self.order,
            next_step=super(MultiStepCheckoutProcess, self).get_first_step())
