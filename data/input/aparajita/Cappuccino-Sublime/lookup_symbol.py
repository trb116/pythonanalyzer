# -*- coding: utf-8 -*-
# lookup_symbol.py
#
# (c) 2014 Aparajita Fishman and licensed under the MIT license.
# URL: http://github.com/aparajita
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

"""This module provides the LookupSymbolCommand class."""

import re
import sublime
import sublime_plugin
import subprocess
from . import util


class LookupSymbolCommand(sublime_plugin.TextCommand):

    """This class implements a command which looks up Cappuccino symbols."""

    DOC_URLS = {
        'dash': 'dash-plugin://keys=macosx,appledoc&query={}',
        'web_base': (
            'https://developer.apple.com/library/mac/documentation/Cocoa/Reference/'
            '{kit}/{types}/{class}_{type}/Reference/Reference.html#//apple_ref/occ/'
        ),
        'class_ref': 'cls/{class}/',
        'protocol_ref': 'intf/{class}/',
        'instance_method_ref': 'instm/{class}/{method}',
        'class_method_ref': 'clm/{class}/{method}',
    }
    MUTABLE_CLASSES = (
        'CPArray',
        'CPDictionary'
    )

    def __init__(self, view):
        """Initialize the command object."""
        super().__init__(view)
        self.search_handlers = {
            'dash': self.dash_lookup,
            'web': self.web_lookup
        }

    def is_enabled(self):
        """Return if this command is available."""
        return (
            sublime.platform() == 'osx' and
            self.view.settings().get('syntax').endswith('/Objective-J.tmLanguage')
        )

    def run(self, edit):
        """Run the command."""
        target = 'dash'  # sublime.load_settings('Cappuccino.sublime-settings').get('lookup_target', 'dash')
        msg = self.lookup(target)

        if msg:
            sublime.error_message(msg)

    def lookup(self, target):
        """Lookup the closest significant symbol in target."""
        region = self.view.sel()[0]
        region = sublime.Region(region.begin(), region.end())
        word_region = self.view.word(region)
        word = self.view.substr(word_region)

        # If the region is empty (a cursor) and is to the right of a non-empty word,
        # move it one character to the left so that the scope is the scope of the word.
        if region.empty() and word and region.begin() == word_region.end():
            region = sublime.Region(region.begin() - 1, region.begin() - 1)

        # Get the scope hierarchy of the beginning of the first selection,
        # then reverse it so searches will find the most specific entity first.
        pt = region.begin()
        scopes = self.view.scope_name(pt).split()
        scopes.reverse()

        klass = None
        protocol = None
        method = None
        search = None
        error = None

        if (
            word.startswith('CP') and
            'meta.implementation.declaration.js.objj' not in scopes and
            'meta.protocl.declaration.js.objj' not in scopes
        ):
            search = word

        elif 'meta.implementation.js.objj' in scopes:
            klass, method, error = util.get_container_and_method(self.view, 'implementation', pt)

        elif 'meta.protocol.js.objj' in scopes:
            protocol, method, error = util.get_container_and_method(self.view, 'protocol', pt)

        elif 'source.js.objj' in scopes:
            search = self.view.substr(self.view.word(region))

        else:
            error = 'You are not within Objective-J source.'

        if error is not None:
            return error
        elif search is not None and target == 'web':
            return 'Plain text searches can only be performed when the lookup_target is "dash".'

        return self.search_handlers[target](klass=klass, protocol=protocol, method=method, search=search)

    def dash_lookup(self, klass=None, protocol=None, method=None, search=None):
        """Lookup search_text in Dash."""
        if search:
            query = search
        else:
            if klass or protocol:
                query = klass or protocol

        if query in self.MUTABLE_CLASSES:
            query = 'CPMutable' + query[2:]

        if method:
            query += ' ' + method

        query = re.sub(r'^CP(.+)', r'NS\1', query, count=1)
        subprocess.call(['/usr/bin/open', self.DOC_URLS['dash'].format(query)])

    def web_lookup(self, klass=None, protocol=None, method=None, search=None):
        """Lookup search_text in the Cocoa web documentation."""
        pass
