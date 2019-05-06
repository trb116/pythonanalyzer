# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('aristotle_mdr', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='glossaryadditionaldefinition',
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name='glossaryadditionaldefinition',
            name='glossaryItem',
        ),
        migrations.RemoveField(
            model_name='glossaryadditionaldefinition',
            name='registrationAuthority',
        ),
        migrations.DeleteModel(
            name='GlossaryAdditionalDefinition',
        ),
        migrations.RemoveField(
            model_name='glossaryitem',
            name='_concept_ptr',
        ),
        migrations.RemoveField(
            model_name='glossaryitem',
            name='superseded_by',
        ),
        migrations.DeleteModel(
            name='GlossaryItem',
        ),
    ]
