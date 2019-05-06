# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import ckeditor_uploader.fields


class Migration(migrations.Migration):

    dependencies = [
        ('aristotle_mdr', '0010_auto_20160106_1814'),
    ]

    operations = [
        migrations.AlterField(
            model_name='_concept',
            name='definition',
            field=ckeditor_uploader.fields.RichTextUploadingField(help_text='Representation of a concept by a descriptive statement which serves to differentiate it from related concepts', verbose_name='definition'),
        ),
        migrations.AlterField(
            model_name='conceptualdomain',
            name='comments',
            field=ckeditor_uploader.fields.RichTextUploadingField(help_text='Descriptive comments about the metadata item.', blank=True),
        ),
        migrations.AlterField(
            model_name='conceptualdomain',
            name='references',
            field=ckeditor_uploader.fields.RichTextUploadingField(blank=True),
        ),
        migrations.AlterField(
            model_name='dataelement',
            name='comments',
            field=ckeditor_uploader.fields.RichTextUploadingField(help_text='Descriptive comments about the metadata item.', blank=True),
        ),
        migrations.AlterField(
            model_name='dataelement',
            name='references',
            field=ckeditor_uploader.fields.RichTextUploadingField(blank=True),
        ),
        migrations.AlterField(
            model_name='dataelementconcept',
            name='comments',
            field=ckeditor_uploader.fields.RichTextUploadingField(help_text='Descriptive comments about the metadata item.', blank=True),
        ),
        migrations.AlterField(
            model_name='dataelementconcept',
            name='references',
            field=ckeditor_uploader.fields.RichTextUploadingField(blank=True),
        ),
        migrations.AlterField(
            model_name='dataelementderivation',
            name='comments',
            field=ckeditor_uploader.fields.RichTextUploadingField(help_text='Descriptive comments about the metadata item.', blank=True),
        ),
        migrations.AlterField(
            model_name='dataelementderivation',
            name='inputs',
            field=models.ManyToManyField(related_name='input_to_derivation', to='aristotle_mdr.DataElement', blank=True),
        ),
        migrations.AlterField(
            model_name='dataelementderivation',
            name='references',
            field=ckeditor_uploader.fields.RichTextUploadingField(blank=True),
        ),
        migrations.AlterField(
            model_name='datatype',
            name='comments',
            field=ckeditor_uploader.fields.RichTextUploadingField(help_text='Descriptive comments about the metadata item.', blank=True),
        ),
        migrations.AlterField(
            model_name='datatype',
            name='references',
            field=ckeditor_uploader.fields.RichTextUploadingField(blank=True),
        ),
        migrations.AlterField(
            model_name='measure',
            name='definition',
            field=ckeditor_uploader.fields.RichTextUploadingField(help_text='Representation of a concept by a descriptive statement which serves to differentiate it from related concepts', verbose_name='definition'),
        ),
        migrations.AlterField(
            model_name='objectclass',
            name='comments',
            field=ckeditor_uploader.fields.RichTextUploadingField(help_text='Descriptive comments about the metadata item.', blank=True),
        ),
        migrations.AlterField(
            model_name='objectclass',
            name='references',
            field=ckeditor_uploader.fields.RichTextUploadingField(blank=True),
        ),
        migrations.AlterField(
            model_name='property',
            name='comments',
            field=ckeditor_uploader.fields.RichTextUploadingField(help_text='Descriptive comments about the metadata item.', blank=True),
        ),
        migrations.AlterField(
            model_name='property',
            name='references',
            field=ckeditor_uploader.fields.RichTextUploadingField(blank=True),
        ),
        migrations.AlterField(
            model_name='registrationauthority',
            name='definition',
            field=ckeditor_uploader.fields.RichTextUploadingField(help_text='Representation of a concept by a descriptive statement which serves to differentiate it from related concepts', verbose_name='definition'),
        ),
        migrations.AlterField(
            model_name='unitofmeasure',
            name='comments',
            field=ckeditor_uploader.fields.RichTextUploadingField(help_text='Descriptive comments about the metadata item.', blank=True),
        ),
        migrations.AlterField(
            model_name='unitofmeasure',
            name='references',
            field=ckeditor_uploader.fields.RichTextUploadingField(blank=True),
        ),
        migrations.AlterField(
            model_name='valuedomain',
            name='comments',
            field=ckeditor_uploader.fields.RichTextUploadingField(help_text='Descriptive comments about the metadata item.', blank=True),
        ),
        migrations.AlterField(
            model_name='valuedomain',
            name='references',
            field=ckeditor_uploader.fields.RichTextUploadingField(blank=True),
        ),
        migrations.AlterField(
            model_name='workgroup',
            name='definition',
            field=ckeditor_uploader.fields.RichTextUploadingField(help_text='Representation of a concept by a descriptive statement which serves to differentiate it from related concepts', verbose_name='definition'),
        ),
        migrations.AlterField(
            model_name='workgroup',
            name='registrationAuthorities',
            field=models.ManyToManyField(related_name='workgroups', verbose_name='Registration Authorities', to='aristotle_mdr.RegistrationAuthority', blank=True),
        ),
    ]
