# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('aristotle_mdr', '0003_auto_20150416_0024'),
    ]

    operations = [
        migrations.AddField(
            model_name='status',
            name='until_date',
            field=models.DateField(null=True, verbose_name='Date registration expires', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='status',
            name='changeDetails',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='status',
            name='registrationDate',
            field=models.DateField(verbose_name='Date registration effective'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='status',
            unique_together=set([]),
        ),
    ]
