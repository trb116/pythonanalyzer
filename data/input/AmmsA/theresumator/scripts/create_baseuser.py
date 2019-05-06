from django.db.utils import OperationalError
from solo.admin import SingletonModelAdmin

from resumator.models import BasicInformation
from resumator.models import Settings

# make BasicInformation singleton if it does not already exist
try:
    basic_information = BasicInformation.get_solo()
except OperationalError:
    pass

# make setting singleton if it does not already exist
try:
    settings = Settings.get_solo()
except OperationalError:
    pass
