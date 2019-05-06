from ..source import Source
from ..iterator import icompact
from ..vimh import command_output


class Vimcmd(Source):
    include_syntax = 'syntax/vim.vim'

    def populate_candidates(self):
        self.candidates = list(icompact(command_output(self.args[0]).split('\n')))
