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

import copy
import warnings
import logging

from django.utils import six, tree

from sellmo.utils.query import PKIterator
from sellmo.utils.version import get_version

from .constants import ORDER_PATTERN, SELLMO_VERSION_PICKLE_KEY
from .utils import split_expression
from .fields import ModelField

REPR_OUTPUT_SIZE = 20

logger = logging.getLogger('sellmo')


class SQ(tree.Node):
    """
    Encapsulates filters as objects that can then be combined logically (using
    & and |).
    """
    # Connection types
    AND = 'AND'
    OR = 'OR'
    default = AND

    _facetted = None
    _facet = None

    def __init__(self, *args, **kwargs):
        super(SQ, self).__init__(
            children=list(args) + list(six.iteritems(kwargs))
        )

    def facetted_only(self, facet=None):
        clone = self.clone()
        clone._facetted = True
        clone._facet = facet
        return clone

    def facetted_exclude(self, facet=None):
        clone = self.clone()
        clone._facetted = False
        clone._facet = facet
        return clone

    def combine(self, other, conn=None):
        if conn is None:
            conn = self.default
        if not isinstance(other, SQ):
            raise TypeError(other)
        obj = type(self)()
        obj.connector = conn
        obj.add(self, conn)
        obj.add(other, conn)
        return obj

    def deconstruct(self, parse_cb, join_cb, facetted=False, facet=None):
        fragments = []
        if (
            self._facetted is None or not facetted and not self._facetted or
            facetted and (
                (
                    self._facetted and (
                        self._facet is None or self._facet == facet
                    )
                ) or (
                    not self._facetted and self._facet is not None and
                    self._facet != facet
                )
            )
        ):
            for child in self.children:
                if hasattr(child, 'deconstruct'):
                    fragments.append(
                        child.deconstruct(
                            parse_cb,
                            join_cb,
                            facetted=facetted,
                            facet=facet
                        )
                    )
                else:
                    field, operator = split_expression(child[0])
                    value = child[1]
                    fragment = parse_cb(field, operator, value)
                    fragments.append(fragment)

        return join_cb(fragments, conn=self.connector, negated=self.negated)

    def __repr__(self):
        return self.deconstruct(
            (
                lambda field, operator, value: '%s__%s=%s' % (field, operator, value)
            ), (
                lambda fragments, conn, negated: '(%s)' % (' %s ' % conn).join(fragments)
            )
        )

    def __or__(self, other):
        return self.combine(other, self.OR)

    def __and__(self, other):
        return self.combine(other, self.AND)

    def __invert__(self):
        obj = type(self)()
        obj.add(self, self.AND)
        obj.negate()
        return obj

    def clone(self):
        clone = self.__class__._new_instance(
            children=[],
            connector=self.connector,
            negated=self.negated
        )
        clone._facetted = self._facetted
        clone._facet = self._facet
        for child in self.children:
            if hasattr(child, 'clone'):
                clone.children.append(child.clone())
            else:
                clone.children.append(child)
        return clone


class SearchQuery(object):
    def __init__(self):
        self.query_filter = SQ()
        self.order_by = []
        self.facets = []
        self.fields = []
        self.low_mark, self.high_mark = 0, None

    def add_filter(self, sq, conn=None):
        self.query_filter = self.query_filter.combine(sq, conn)

    def add_ordering(self, *ordering):
        errors = []
        for item in ordering:
            if not ORDER_PATTERN.match(item):
                errors.append(item)
        if errors:
            raise ValueError('Invalid order_by arguments: %s' % errors)
        if ordering:
            self.order_by.extend(ordering)

    def add_facets(self, *facets):
        if facets:
            self.facets.extend(facets)

    def add_fields(self, *fields):
        if fields:
            self.fields.extend(fields)

    def set_limits(self, low=None, high=None):
        if high is not None:
            if self.high_mark is not None:
                self.high_mark = min(self.high_mark, self.low_mark + high)
            else:
                self.high_mark = self.low_mark + high
        if low is not None:
            if self.high_mark is not None:
                self.low_mark = min(self.high_mark, self.low_mark + low)
            else:
                self.low_mark = self.low_mark + low

    def clone(self, klass=None, **kwargs):
        obj = (klass or type(self))()
        obj.query_filter = self.query_filter.clone()
        obj.order_by = self.order_by[:]
        obj.facets = self.facets[:]
        obj.fields = self.fields[:]
        obj.low_mark, obj.high_mark = self.low_mark, self.high_mark
        return obj


class SearchQueryList(list):
    def __init__(self, data=None, facets=None):
        super(SearchQueryList, self).__init__(data)
        self._facets = facets
        if facets is None and isinstance(data, BaseIterator):
            self._facets = data.facets

    def facets(self):
        return dict(self._facets) if self._facets is not None else {}

    def __getitem__(self, k):
        result = super(SearchQueryList, self).__getitem__(k)
        if isinstance(k, slice):
            result = SearchQueryList(result, facets=self.facets())
        return result


class BaseIterator(object):

    base_fields = []

    def __init__(self, documents, index, query, raw=False):
        self.documents = documents
        self.index = index
        self.query = query
        self.raw = raw
        self.facets = None


class FetchIterator(BaseIterator):
    def __iter__(self):
        rows, facets = self.index.adapter.fetch_index(self.index, self.query)
        if not self.raw:
            rows, facets = self.fetch_models(rows, facets)
        self.facets = facets
        for row in rows:
            yield row

    def fetch_models(self, rows, facets):

        fk_pks = {}
        fk_objs = {}
        documents = None
        document_pks = None

        for field_name in set(self.query.fields + self.query.facets):
            field = self.index.fields[field_name]
            if field_name == 'document':
                document_pks = set([row[field_name] for row in rows])
            elif isinstance(field, ModelField):
                if field.model not in fk_pks:
                    fk_pks[field.model] = set()
                    fk_objs[field.model] = {}
                if field_name in self.query.fields:
                    fk_pks[field.model] |= set(
                        [
                            row[field_name] for row in rows
                        ]
                    )
                if field_name in self.query.facets:
                    fk_pks[field.model] |= set(
                        value[0]
                        for value in facets[field_name] if value[0] is not None
                    )

        # Fetch regular models
        for model, pks in six.iteritems(fk_pks):
            for obj in PKIterator(model.objects.all(), pks):
                fk_objs[model][obj.pk] = obj

        # Fetch documents from given documents queryset
        if document_pks is not None:
            documents = {
                document.pk: document
                for document in PKIterator(self.documents, document_pks)
            }

        new_facets = {}
        for facet_name, raw_values in six.iteritems(facets):
            field = self.index.fields[facet_name]
            if isinstance(field, ModelField):
                values = []
                for value, count in raw_values:
                    if value in fk_objs[field.model]:
                        value = fk_objs[field.model][value]
                    elif value is not None:
                        logger.warning(
                            "Index %s is dirty, value %s for %s no longer exists"
                            % (self.index, value, facet_name)
                        )
                        continue
                    values.append((value, count))
            else:
                values = raw_values
            new_facets[facet_name] = values

        new_rows = []
        for row in rows:
            new_row = {}
            for field_name, value in six.iteritems(row):
                field = self.index.fields[field_name]
                if field_name == 'document':
                    if value in documents:
                        value = documents[value]
                    else:
                        # Invalid row
                        new_row = None
                        logger.warning(
                            "Index %s is dirty, document %s no longer exists" %
                            (self.index, value))
                        break
                elif isinstance(field, ModelField) and value is not None:
                    if value in fk_objs[field.model]:
                        value = fk_objs[field.model][value]
                    else:
                        logger.warning(
                            "Index %s is dirty, value %s for %s no longer exists"
                            % (self.index, value, field_name)
                        )
                new_row[field_name] = value

            if new_row is not None:
                new_rows.append(new_row)

        return new_rows, new_facets


class ValuesIterator(FetchIterator):
    pass


class ModelIterator(FetchIterator):

    base_fields = ['document']

    def __iter__(self):
        for row in super(ModelIterator, self).__iter__():
            obj = row['document']
            values = dict(row)
            values.pop('document')
            obj._index = self.index
            obj._index_values = values
            yield obj


class SearchQuerySet(object):

    model_iterator_class = ModelIterator
    values_iterator_class = ValuesIterator

    def __init__(self, index, documents):
        self.index = index
        self.documents = documents
        self.query = SearchQuery()
        self._iterator_class = self.model_iterator_class
        self._result_cache = None
        self._raw = False

    def __deepcopy__(self, memo):
        """
        Deep copy of a QuerySet doesn't populate the cache
        """
        obj = type(self)(self.index, self.documents)
        for k, v in self.__dict__.items():
            if k == '_result_cache':
                obj.__dict__[k] = None
            else:
                obj.__dict__[k] = copy.deepcopy(v, memo)
        return objz

    def __getstate__(self):
        """
        Allows the QuerySet to be pickled.
        """
        # Force the cache to be fully populated.
        self._fetch_all()
        obj_dict = self.__dict__.copy()
        obj_dict[SELLMO_VERSION_PICKLE_KEY] = get_version()
        return obj_dict

    def __setstate__(self, state):
        msg = None
        pickled_version = state.get(SELLMO_VERSION_PICKLE_KEY)
        if pickled_version:
            current_version = get_version()
            if current_version != pickled_version:
                msg = (
                    "Pickled queryset instance's Django version %s does"
                    " not match the current version %s." %
                    (pickled_version, current_version)
                )
        else:
            msg = "Pickled queryset instance's Django version is not specified."

        if msg:
            warnings.warn(msg, RuntimeWarning, stacklevel=2)

        self.__dict__.update(state)

    def __repr__(self):
        data = list(self[:REPR_OUTPUT_SIZE + 1])
        if len(data) > REPR_OUTPUT_SIZE:
            data[-1] = "...(remaining elements truncated)..."
        return repr(data)

    def __len__(self):
        self._fetch_all()
        return len(self._result_cache)

    def __iter__(self):
        self._fetch_all()
        return iter(self._result_cache)

    def __bool__(self):
        self._fetch_all()
        return bool(self._result_cache)

    def __nonzero__(self): # Python 2 compatibility
        return type(self).__bool__(self)

    def __getitem__(self, k):
        if not isinstance(k, (slice, ) + six.integer_types):
            raise TypeError
        assert ((not isinstance(k, slice) and (k >= 0)) or
                (isinstance(k, slice) and (k.start is None or k.start >= 0) and
                 (k.stop is None or k.stop >= 0))), \
            "Negative indexing is not supported."

        if self._result_cache is not None:
            return self._result_cache[k]

        if isinstance(k, slice):
            qs = self._clone()
            if k.start is not None:
                start = int(k.start)
            else:
                start = None
            if k.stop is not None:
                stop = int(k.stop)
            else:
                stop = None
            qs.query.set_limits(start, stop)
            if k.step:
                qs._fetch_all()
                return qs._result_cache[::k.step]
            else:
                return qs

        qs = self._clone()
        qs.query.set_limits(k, k + 1)
        return list(qs)[0]

    def facets(self):
        self._fetch_all()
        return self._result_cache.facets()

    def count(self):
        if self._result_cache is not None:
            return len(self._result_cache)
        return self.index.adapter.fetch_count(
            self.index, self._get_fetch_query()
        )

    def iterator(self, iterator_class=None):
        if iterator_class is None:
            iterator_class = self._iterator_class
        return iterator_class(
            self.documents, self.index, self._get_fetch_query(iterator_class)
        )

    ###################
    # PRIVATE METHODS #
    ###################

    def _get_fetch_query(self, iterator_class=None):
        query = self.query.clone()
        if iterator_class is None:
            iterator_class = self._iterator_class
        query.add_fields(*iterator_class.base_fields)
        return query

    def _fetch_all(self):
        if self._result_cache is None:
            self._result_cache = SearchQueryList(self.iterator())

    def _clone(self):
        clone = type(self)(self.index, self.documents)
        clone._iterator_class = self._iterator_class
        clone._raw = self._raw
        clone.query = self.query.clone()
        return clone

    def _filter_or_exclude(self, negate, *args, **kwargs):
        clone = self._clone()
        if negate:
            clone.query.add_filter(~SQ(*args, **kwargs))
        else:
            clone.query.add_filter(SQ(*args, **kwargs))
        return clone

    ##################################################################
    # PUBLIC METHODS THAT ALTER ATTRIBUTES AND RETURN A NEW QUERYSET #
    ##################################################################

    def all(self):
        return self._clone()

    def filter(self, *args, **kwargs):
        return self._filter_or_exclude(False, *args, **kwargs)

    def exclude(self, *args, **kwargs):
        return self._filter_or_exclude(True, *args, **kwargs)

    def order_by(self, *args):
        clone = self._clone()
        clone.query.add_ordering(*args)
        return clone

    def with_facets(self, *args):
        clone = self._clone()
        clone.query.add_facets(*args)
        return clone

    def with_fields(self, *args):
        clone = self._clone()
        clone.query.add_fields(*args)
        return clone

    def values(self):
        clone = self._clone()
        clone._iterator_class = self.values_iterator_class
        return clone

    def raw(self):
        clone = self._clone()
        clone._raw = True
        return clone

    ################################
    # PUBLIC METHODS THAT DO QUERIES
    ################################

    def first(self):
        """
        Returns the first object of a query, returns None if no match is found.
        """
        objects = list((self if self.ordered else self.order_by('document'))[:1
                                                                             ])
        if objects:
            return objects[0]
        return None

    def last(self):
        """
        Returns the last object of a query, returns None if no match is found.
        """
        objects = list(
            (
                self.reverse() if self.ordered else self.order_by(
                    '-document'
                )
            )[:1]
        )
        if objects:
            return objects[0]
        return None

    ###################################
    # PUBLIC INTROSPECTION ATTRIBUTES #
    ###################################

    def ordered(self):
        """
        Returns True if the QuerySet is ordered -- i.e. has an order_by()
        clause or a default ordering on the model.
        """
        return self.query.order_by

    def can_use_field(self, field_name, field=None):
        return self.index.has_field(field_name, field)

    ordered = property(ordered)
