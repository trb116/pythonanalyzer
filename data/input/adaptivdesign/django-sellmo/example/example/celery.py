"""
Celery config for example project.
"""

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "example.settings")

from sellmo import params
from sellmo.celery.integration import app

params.worker = True
