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

import abc

from django.utils.module_loading import import_string

from sellmo.conf import get_setting


class AbstractIndexAdapter(object):

    __metaclass__ = abc.ABCMeta

    @property
    def supports_runtime_build(self):
        return False

    def initialize_index(self, index):
        """
        Called for each new index. Allows
        for intialization purposes.
        """
        pass

    @abc.abstractmethod
    def introspect_index(self, index):
        """
        The adapter needs introspect it's existing index
        structure and return a dictionary of index fields.
        If the index does not exist it should return False.
        """
        pass

    @abc.abstractmethod
    def build_index(
        self,
        index,
        added_fields=None,
        deleted_fields=None,
        changed_fields=None,
        exists=False
    ):
        """
        Build internal index structure. Returns True if index was succesfully
        build.
        """
        pass

    @abc.abstractmethod
    def sync_index(self, index, documents, full=False):
        """
        (Re)indexes each document from the given iterable.
        A document can be either a model or it's pk.
        """
        pass

    @abc.abstractmethod
    def fetch_index(self, index, query):
        """
        Searches the index for documents matching the given query.
        Should return a tuple containing an iterable of document
        pk's, a values dictionary and a facets dictionary.
        """
        pass

    @abc.abstractmethod
    def fetch_index_count(self, index, query):
        """
        Searches the index for documents matching the given query.
        But only returns the number of matches found.
        """
        pass


DefaultIndexAdapter = import_string(
    get_setting(
        'DEFAULT_INDEX_ADAPTER',
        default='sellmo.core.indexing.adapters.database.DatabaseIndexAdapter'
    )
)
