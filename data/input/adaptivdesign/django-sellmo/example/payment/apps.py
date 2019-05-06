from django.utils.translation import ugettext_lazy as _

from sellmo.core.apps import SellmoAppConfig


class DefaultConfig(SellmoAppConfig):
    name = 'payment'
