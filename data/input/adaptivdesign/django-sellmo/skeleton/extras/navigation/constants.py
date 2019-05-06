from django.conf import settings
from django.utils.translation import ugettext_lazy as _


PLACEMENT_CHOICES = getattr(settings, 'NAVIGATION_PLACEMENT_CHOICES', [('default', _("default"))])
MAX_EXPIRE_TIME = getattr(settings, 'NAVIGATION_MAX_EXPIRE_TIME', 3600 * 24)
