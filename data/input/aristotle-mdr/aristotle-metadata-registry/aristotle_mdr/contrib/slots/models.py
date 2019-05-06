"""
Aristotle MDR 11179 Slots models
================================

These are based on the Slots definition in ISO/IEC 11179 Part 3 - 7.2.2.4
"""

from django.apps import apps
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from django.conf.global_settings import LANGUAGES

from model_utils import Choices
from model_utils.models import TimeStampedModel

from aristotle_mdr import models as MDR


class SlotDefinition(TimeStampedModel):
    CARDINALITY = Choices(
        (0, 'singleton', _('Singleton (0..1)')),
        (1, 'repeatable', _('Repeatable (0..n)')),
    )

    app_label = models.CharField(
        max_length=256,
        help_text=_('Add an app for app specific help, required for concept help')
        )
    concept_type = models.CharField(max_length=256)
    slot_name = models.CharField(max_length=256)  # Or some other sane length
    help_text = models.TextField(max_length=256, null=True, blank=True)  # Or some other sane length
    datatype = models.ForeignKey(MDR.DataType, null=True, blank=True)  # What! So meta
    cardinality = models.IntegerField(
        choices=CARDINALITY,
        default=CARDINALITY.singleton,
        help_text=_("Specifies if the slot can be stored multiple times.")
    )

    def __str__(self):
        return "{0.slot_name}".format(self)

    def clean(self):
        print ContentType.objects.filter(model=self.concept_type).all()
        if not ContentType.objects.filter(app_label=self.app_label, model=self.concept_type).exists():
            raise ValidationError(_('The concept type specified below does not exist.'))

    def model_class(self):
        return ContentType.objects.get(app_label=self.app_label, model=self.concept_type)


class Slot(TimeStampedModel):
    # on save confirm the concept and model are correct, otherwise reject
    # on save confirm the cardinality
    type = models.ForeignKey(SlotDefinition)
    concept = models.ForeignKey(MDR._concept, related_name='slots')
    value = models.CharField(max_length=256)

    def clean(self):
        if hasattr(self, 'type') and self.type is not None and not self.concept.__class__ != self.type.model_class():
            raise ValidationError('This slot is not allowed on this model')

    def __str__(self):
        return "{0.type}.{0.value}".format(self)
