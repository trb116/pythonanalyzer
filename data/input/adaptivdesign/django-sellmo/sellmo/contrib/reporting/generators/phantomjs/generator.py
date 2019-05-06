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

import os.path
import codecs

from sellmo.conf import get_setting
from sellmo.contrib.reporting.generators import AbstractReportGenerator

from .pipe import pipe, PipeError

PARAMS = {
    'pdf': {
        'size': 'A4',
        'orientation': 'portrait',
        'margin': '1cm',
        'zoom': 1.0,
    },
    'png': {
        'viewport': '800x800'
    }
}

phantomjs_params = get_setting('PARAMS', default=PARAMS, prefix='PHANTOMJS')

phantomjs_executable = get_setting(
    'PARAMS',
    default='phantomjs',
    prefix='PHANTOMJS'
)


class PhantomJSReportGenerator(AbstractReportGenerator):
    @property
    def input_formats(self):
        return ['html']

    @property
    def output_formats(self):
        return ['pdf', 'png']

    def get_params(self, writer, frmt):
        params = super(PhantomJSReportGenerator, self).get_params(writer, frmt)
        suggest_params = phantomjs_params.get(frmt, {})
        for param, suggest in suggest_params.iteritems():
            value = writer.negotiate_param(param, suggest, **params)
            params[param] = value if not value is False else suggest

        return params

    def get_data(self, writer, format):
        html = super(PhantomJSReportGenerator, self).get_data(writer, frmt)
        params = self.get_params(writer, frmt)

        # Create command
        script = os.path.join(os.path.dirname(__file__), 'scripts/render.js')
        arguments = ['format={0}'.format(frmt)]

        # Create command arguments
        for param, value in params.iteritems():
            arguments += ['{0}={1}'.format(param, params[param])]
        arguments = ' '.join(arguments)

        # Encode as UTF8
        html = codecs.encode(html, 'utf8')

        try:
            return pipe(
                '{0} {1} {2}'.format(phantomjs_executable, script, arguments),
                input=html
            )
        except PipeError:
            raise

    def get_extension(self, format):
        return '.' + frmt

    def get_mimetype(self, format):
        if frmt == 'pdf':
            return 'application/pdf'
        elif frmt == 'png':
            return 'image/png'
