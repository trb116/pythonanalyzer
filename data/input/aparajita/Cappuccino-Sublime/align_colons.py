# -*- coding: utf-8 -*-
# align_colons.py
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

"""This module provides the BalanceBracketsCommand class."""

import re
import sublime
import sublime_plugin
from . import util


class AlignColonsCommand(sublime_plugin.TextCommand):

    """This class implements a command which aligns colons in a message send."""

    BRACKET_RE = re.compile(r'[\[\]]')

    def __init__(self, view):
        """Initialize the command object."""
        super().__init__(view)

    def run(self, edit, char='\n'):
        """Run the command."""

        pt = self.view.sel()[0].begin()

        if char == '\n':
            if self.run_linefeed_align(edit, pt):
                return
        elif self.run_colon_align(edit, pt):
            return

        self.view.run_command('insert', {'characters': char})

    def run_linefeed_align(self, edit, pt):
        """Align colons when enter/return is pressed."""
        char = self.view.substr(pt)

        # When we get here, we could be:
        #   - before a name
        #   - within a name
        #   - between a name and a colon

        if char == ':':
            word_pt = self.view.find_by_class(pt, False, sublime.CLASS_WORD_START)
        elif char.isspace():
            # Could be before or after a name, see if before
            region = self.view.find(r'[ \t]+\w', pt)
            forward = region and region.begin() == pt
            word_pt = self.view.find_by_class(pt, forward, sublime.CLASS_WORD_START)
        else:
            # Within a name
            word_pt = pt

        # The only valid scope for the name is 'entity.name.function.name-of-parameter.js.objj'
        scope = self.view.scope_name(word_pt).split()[-1]

        return (
            scope == 'entity.name.function.name-of-parameter.js.objj' and
            self.linefeed_align(edit, pt)
        )

    def linefeed_align(self, edit, pt):
        """
        Vertically align colons.

        The first colon to the right of pt is aligned with
        the first colon to the left. If within a message send,
        align with the first colon within the closest square bracket.

        """

        # First get the colon to the left that we will align with
        anchor_pt = self.find_anchor_pt(pt)

        if anchor_pt is None:
            return

        # Now find the colon to the right
        region = self.view.find(':', pt)

        if region is None:
            return

        align_pt = region.begin()

        # Skip whitespace to the right of the cursor
        whitespace = self.view.find(r'[ \t]+', pt)

        if whitespace and whitespace.begin() == pt:
            pt += whitespace.size()
            util.select_pt(self.view, pt)

        line_start = self.view.line(pt).begin()
        tab_spaces = ' ' * self.view.settings().get('tab_size', 4)
        indent = ''

        # If auto indent is on, subtract leading whitespace
        if self.view.settings().get('auto_indent'):
            region = self.view.find(r'^[ \t]+', line_start)

            if region and region.begin() == line_start:
                indent = self.view.substr(region)

        # Calculate how many spaces we need to insert to align the left and right colons
        anchor_pos = anchor_pt - line_start
        chars_before_colon = align_pt - pt
        num_spaces = anchor_pos - chars_before_colon - len(indent)
        text = '\n' + indent + (' ' * num_spaces)

        # Convert spaces to tabs if necessary
        if not self.view.settings().get('translate_tabs_to_spaces'):
            text = text.replace(tab_spaces, '\t')

        self.view.replace(edit, sublime.Region(pt, pt), text)
        util.select_pt(self.view, pt + len(text))
        return True

    def run_colon_align(self, edit, pt):
        """Align colons when a ":" is typed."""

        # Bail if there are any brackets before the : on the line
        line = self.view.line(pt)
        preceding_text = self.view.substr(sublime.Region(line.begin(), pt))

        if self.BRACKET_RE.search(preceding_text):
            return
        else:
            line_end = self.view.find_by_class(pt, False, sublime.CLASS_LINE_END)
            anchor_pt = self.find_anchor_pt(line_end)

            if anchor_pt is None:
                return

            # Calculate how far and in which direction to move. Note that
            # we have to expand tabs when calculating offsets within the line
            # so that the offsets between lines are consistent.
            anchor_offset = util.line_offset(self.view, anchor_pt, expand_tabs=True)
            line = self.view.line(pt)
            offset = util.line_offset(self.view, pt, expand_tabs=True)
            move = anchor_offset - offset

            if move == 0:
                return

            # Get the indent for this line
            indent_region = self.view.find(r'^[ \t]*', line.begin())
            indent = self.view.substr(indent_region)
            old_indent = indent

            # Add or remove from the indent, but convert tabs to spaces
            # first since move assumes all spaces.
            tab_spaces = ' ' * self.view.settings().get('tab_size', 4)

            if not self.view.settings().get('translate_tabs_to_spaces'):
                indent = indent.replace('\t', tab_spaces)

            if move > 0:
                indent += (' ' * move)
            else:
                indent = indent[-move:]

            if not self.view.settings().get('translate_tabs_to_spaces'):
                indent = indent.replace(tab_spaces, '\t')

            # Replace the current line with the moved line
            region = sublime.Region(indent_region.end(), pt)
            text = indent + self.view.substr(region) + ':'
            region = sublime.Region(pt, line.end())
            text += self.view.substr(region)
            self.view.replace(edit, line, text)

            # Move the selection by how much the indent changed + 1 for the ':'.
            util.select_pt(self.view, pt + (len(indent) - len(old_indent)) + 1)
            return True

    def find_anchor_pt(self, pt):
        """Return the point of the colon to the left of pt that can be aligned with."""
        line_start = self.view.line(pt).begin()

        # Go back towards the beginning of the line
        # until we find a ":" not within a string.
        last_match = None

        for pt in range(pt - 1, line_start - 1, -1):
            char = self.view.substr(pt)

            if char == '[':
                break

            if char != ':' or self.view.score_selector(pt, 'string') != 0:
                continue

            # Now we are before a colon, back up to the beginning of the previous word
            # and see what its scope is.
            word_start = self.view.find_by_class(pt, False, sublime.CLASS_WORD_START)
            scope = self.view.scope_name(word_start).split()[-1]

            if scope in ('entity.name.function.js.objj', 'entity.name.function.name-of-parameter.js.objj'):
                # Okay, we are within the correct scope, but there may be more on this line
                last_match = pt

        return last_match
