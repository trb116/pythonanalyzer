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

from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string

from sellmo.conf import get_setting

from .report import Report


class AbstractReportGenerator(object):

    __metaclass__ = abc.ABCMeta

    def __init__(self, writer):
        self.writer = writer

    @abc.abstractproperty
    def input_formats(self):
        pass

    @abc.abstractproperty
    def output_formats(self):
        pass

    def generate_report(self, frmt, context=None):
        with self.writer.open(frmt, context) as writer:
            return Report(
                self.get_filename(writer, frmt), self.get_data(writer, frmt),
                self.get_mimetype(frmt)
            )

    def get_params(self, writer, frmt):
        return {}

    def get_data(self, writer, frmt):
        params = self.get_params(writer, frmt)
        if params is None:
            params = {}
        return writer.get_data(**params)

    def get_filename(self, writer, frmt):
        ext = self.get_extension(frmt)
        if not ext or not ext.startswith('.'):
            raise ValueError("Invalid extension")
        return writer.get_name() + ext

    @abc.abstractmethod
    def get_extension(self, frmt):
        pass

    @abc.abstractmethod
    def get_mimetype(self, frmt):
        pass


class ReportGenerators(list):
    def __init__(self, generators):
        super(ReportGenerators, self).__init__(
            [
                import_string(generator) for generator in generators
            ]
        )

        self.input_formats = {}
        self.output_formats = {}

        # Map generators
        for generator in self:
            if not generator.input_formats or not generator.output_formats:
                raise ImproperlyConfigured(
                    "Generator needs input and output formats"
                )

            # Map to input formats
            for frmt in generator.input_formats:
                if frmt not in self.input_formats:
                    self.input_formats[frmt] = set()
                self.input_formats[frmt].add(generator)

            # Map to output formats
            for frmt in generator.output_formats:
                if frmt not in self.output_formats:
                    self.output_formats[frmt] = set()
                self.output_formats[frmt].add(generator)


generators = ReportGenerators(get_setting('REPORT_GENERATORS', default=[]))
