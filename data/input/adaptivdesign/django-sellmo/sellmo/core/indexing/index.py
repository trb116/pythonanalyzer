# Copyright (c) 2014, Adaptiv Design
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.

# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.

# 3. Neither the name of the copyright holder nor the names of its contributors
# may be used to endorse or promote products derived from this software without
# specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import logging
import copy
import itertools
from collections import OrderedDict

from django.utils import six
from django.db import models
from django.db.models import QuerySet

from sellmo.core.debouncing import debounced

from .fields import IndexField, ModelField
from .search import SearchQuerySet
from .exceptions import IndexFieldError, IndexInvalidated

logger = logging.getLogger('sellmo')


class IndexMetaClass(type):
    def __new__(mcs, name, bases, attrs):

        # Collect fields from current class.
        current_fields = []
        for key, value in list(attrs.items()):
            if isinstance(value, IndexField):
                current_fields.append((key, value))
                attrs.pop(key)
        current_fields.sort(key=lambda x: x[1].creation_counter)
        attrs['declared_fields'] = OrderedDict(current_fields)

        new_class = (
            super(IndexMetaClass, mcs).__new__(mcs, name, bases, attrs)
        )

        if bases == (object, ):
            return new_class

        # Walk through the MRO.
        declared_fields = OrderedDict()
        for base in reversed(new_class.__mro__):
            # Collect fields from base class.
            if hasattr(base, 'declared_fields'):
                declared_fields.update(base.declared_fields)

            # Field shadowing.
            for attr, value in base.__dict__.items():
                if value is None and attr in declared_fields:
                    declared_fields.pop(attr)

        model = getattr(new_class, 'model', None)
        if model:
            if not issubclass(model, models.Model):
                raise ValueError('Index model %s is not a model.' % model)
            # Create document field
            declared_fields['document'] = ModelField(
                model,
                required=True,
                populate_value_cb=(lambda document, **variety: document)
            )

        new_class.base_fields = declared_fields
        new_class.declared_fields = declared_fields

        return new_class


def index_unpickle(name):
    from sellmo.core.indexing import indexer
    return indexer.get_index(name)


class Index(six.with_metaclass(IndexMetaClass, object)):

    model = None
    SearchQuerySet = SearchQuerySet

    # Will be the intersection of runtime and introspected fields
    # and shall only be used.
    fields = None
    runtime_fields = None
    introspected_fields = None

    _invalidated = False

    def __init__(self, name, adapter):
        if self.model is None:
            raise ValueError("Index has no model class specified.")
        self.name = name
        self.adapter = adapter
        self.fields = self.get_fields()

    # Provide pickle support
    def __reduce__(self):
        return (index_unpickle, (self.name, ))

    def get_fields(self):
        return copy.deepcopy(self.base_fields)

    def has_field(self, field_name, field=None):
        if field_name in self.fields:
            a = field
            b = self.fields[field_name] if field else None
            return a == b
        return False

    def populate(self, document, values, **variety):
        return values

    def build_records(self, document):
        if isinstance(document, (int, long, basestring)):
            try:
                document = self.get_queryset().get(pk=document)
            except self.model.DoesNotExist:
                logger.warning(
                    "Could not build index records for document %s. "
                    "It's model does not exist." % (document)
                )
                return []

        logger.info("Building index records for document %s" % (document))

        # Create all possible varieties
        varieties = itertools.product(
            *[
                [
                    (field_name, variety)
                    for variety in field.get_varieties(document)
                ]
                for field_name, field in six.iteritems(self.fields)
                if field.varieties
            ]
        )

        results = []
        for variety in varieties:

            # Unpack to dict
            variety = {key: value for key, value in variety}

            values = {}
            missing = {}

            # First get values from each seperate field
            for field_name, field in six.iteritems(self.fields):
                if field_name in variety:
                    values[field_name] = variety[field_name]
                else:
                    has_value, value = field.populate_field(
                        document, **variety
                    )
                    if has_value:
                        values[field_name] = value
                    else:
                        missing[field_name] = field

            # Now allow index to provide additonal values
            result = {}
            for field_name, value in six.iteritems(
                self.populate(
                    document, values, **variety
                )
            ):
                if field_name not in self.fields:
                    logger.info(
                        "Value %s for field %s will be omitted from index" %
                        (value, field_name)
                    )
                    continue
                missing.pop(field_name, None)
                result[field_name] = value

            for field_name, field in six.iteritems(missing):
                if field.required:
                    raise IndexFieldError("%s is required" % field_name)
                else:
                    result[field_name] = None

            results.append(result)

        return results

    def _check_not_invalidated(self):
        if self.invalidated:
            raise IndexInvalidated()

    def get_queryset(self):
        return self.model.objects.all()

    def invalidate(self):
        self._invalidated = True
        # Attempt to build the index
        from sellmo.core.indexing import indexer
        indexer.build_index(self.name)

    @property
    def invalidated(self):
        return self._invalidated

    def search(self, documents=None):
        self._check_not_invalidated()
        if documents is not None and not isinstance(documents, QuerySet):
            raise ValueError("Provide a queryset for search operations")
        return self.SearchQuerySet(self, self.get_queryset())

    def _sync_args_cb(self, documents=None):
        if isinstance(documents, (list, set, tuple)):
            # For debouncing we need a set of hasable documents
            # convert to frozenset. Since order does not matter.
            # Also normalize input by trying to retrieve the documents
            # pk.
            documents = frozenset(
                [
                    document.pk if isinstance(document, self.model) else
                    document for document in documents
                ]
            )
        elif isinstance(documents, QuerySet):
            # When a QuerySet is given, we do not want to evaluate it. Instead
            # we still want to have a consistent hashable value. this
            # way identical calls can be detected. With Django's current
            # Query implmentation at django.db.models.sql.query we can
            # simply convert the query intro a unique string.
            documents = str(documents.query)

        return ((self, ), {'documents': documents})

    # Debounce the sync method, since this one will often be called
    # in response to django signals. Such signals can overlap especially
    # django's m2m changed signals. In a lot of cases sync calls are
    # identical.
    @debounced(hashable_args_cb=_sync_args_cb)
    def sync(self, documents=None):
        self._check_not_invalidated()
        self.adapter.sync_index(self,
                                documents or self.get_queryset(),
                                full=(documents is None))

    def __hash__(self):
        return hash(
            (
                self.name, frozenset(
                    (field[0], field[1]) for field in six.iteritems(
                        self.fields)
                )
            )
        )

    def __repr__(self):
        path = '%s.%s' % (self.__class__.__module__, self.__class__.__name__)
        return '<%s>' % path
