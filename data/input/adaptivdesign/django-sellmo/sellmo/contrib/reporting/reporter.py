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

from .constants import DEFAULT_REPORT_FORMAT


class Reporter(object):

    writers = {}

    def get_report(self, report_type, frmt=None, context=None):

        context = context or {}
        frmt = frmt or DEFAULT_REPORT_FORMAT

        # Find all acceptable formats
        input_formats = set([frmt])
        if frmt in REPORT_GENERATORS.output_formats:
            for generator in REPORT_GENERATORS.output_formats[frmt]:
                input_formats = set(generator.input_formats) | input_formats

        # Find writer
        if not report_type in self.writers:
            raise ValueError(
                "No writer for report type '{0}'".format(report_type)
            )
        for input_format in input_formats:
            if input_format in self.writers[report_type]:
                writer = self.writers[report_type][input_format]
                break
        else:
            raise ValueError("Format '{0}' is not supported".format(frmt))

        # Find the generator with both correct input and output
        generators = REPORT_GENERATORS.output_formats[frmt]
        generators &= REPORT_GENERATORS.input_formats[writer.output_format]
        generator = list(generators)[0]

        # Create a new generator and generate report
        generator = generator(writer)
        return generator.generate_report(frmt, context)

    def can_report(self, report_type):
        return report_type in self.writers

    def register_writer(self, report_type, writer):
        if isinstance(writer, (str, unicode)):
            writer = import_string(writer)

        # Map writer to report_type and writer format
        if report_type not in self.writers:
            self.writers[report_type] = {}
        self.writers[report_type][writer.output_format] = writer


reporter = Reporter()
