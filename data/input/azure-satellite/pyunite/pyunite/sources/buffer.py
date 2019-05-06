import re

from ..source import Source
from ..iterator import icompact
from ..vimh import command_output


class Buffer(Source):
    syntaxes = [
        'syntax match buffer_name /[^/ \[\]]\+\s/ contained',
        'syntax match buffer_prefix /\d\+\s\%(\S\+\)\?/ contained',
        'syntax match buffer_info /\[.\{-}\] / contained',
        'syntax match buffer_modified /\[.\{-}+\]/ contained',
        'syntax match buffer_nofile /\[nofile\]/ contained',
        'syntax match buffer_time /(.\{-}) / contained',
    ]


    highlights = [
        'highlight default link buffer_name Function',
        'highlight default link buffer_prefix Constant',
        'highlight default link buffer_info PreProc',
        'highlight default link buffer_modified Statement',
        'highlight default link buffer_nofile Function',
        'highlight default link buffer_time Statement',
    ]


    def populate_candidates(self):
        # Example of a candidate
        # 15 %a   "pyunite/sources/buffer.py"    line 10
        self.candidates = list(icompact(command_output('ls').split('\n')))
