import re
import vim
import funcy as fn
from uuid import uuid4
from itertools import ifilter

from . import ui, option, source


class States(object):
    """ Small wrapper around a list of states """
    def __init__(self):
        self.states = []

    def add(self, state):
        self.states.append(state)

    def remove(self, state, wipeout_buffer=True):
        if not wipeout_buffer:
            state.buff.valid and ui.wipeout_buffer(state.buff)
        self.states.remove(state)

    def remove_invalid(self):
        [ self.remove(s) for s in self.states if s.is_invalid() ]

    def remove_some(self, states):
        [ self.remove(s) for s in list(states) ]

    def get_states(self):
        return self.states


states = States()


class State(object):
    """ Contains all the information ever needed to render a PyUnite window.
    There is a one-to-one relation between PyUnite buffers and states. """

    def __init__(self, source, options):
        self.uid = uuid4()
        self.buff = None
        self.source = source
        self.options = options
        self.container = {
            'global': vim,
            'tabpage': vim.current.tabpage,
            'window': vim.current.window
        }[options['scope']]

    def is_invalid(self):
        # When a tabpage/window/buffer is closed, its 'valid' attribute becomes
        # False.  The 'vim' module does not have a 'valid' attribute, but then
        # again, any state with global scope is valid unless its underlying buffer
        # has been closed.
        return not self.buff.valid or not getattr(self.container, 'valid', True)


def parse_state(cmdline):
    spaces_with_no_backslashes = r'((?<!\\)\s)+'
    tokens = filter(lambda x: x != ' ', re.split(spaces_with_no_backslashes, cmdline))
    options = map(option.parse_option, (ifilter(lambda x: x.startswith('-'), tokens)))
    sources = map(source.parse_source, (ifilter(lambda x: x and not x.startswith('-'), tokens)))
    assert len(sources) > 0, 'You need to specify a source'
    assert len(sources) == 1, 'There can only be one source'
    map(option.validate_option, options)
    return State(sources[0], fn.merge(dict(options), option.default_options))
