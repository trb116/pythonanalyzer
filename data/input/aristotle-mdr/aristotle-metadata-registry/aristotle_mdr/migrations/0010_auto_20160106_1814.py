# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aristotle_mdr', '0009_add_explicit_related_name_for_values'),
    ]

    operations = [
        migrations.AlterField(
            model_name='valuedomain',
            name='description',
            field=models.TextField(help_text='Description or specification of a rule, reference, or range for a set of all values for a Value Domain.', verbose_name='description', blank=True),
        ),
    ]
