import vim
import re
from itertools import ifilter, imap
from functools import partial
from operator import itemgetter, methodcaller
import funcy as fn
from pathlib import Path

from . import vimh, misc, option, source, state, ui, sources, iterator
from .state import states


@vimh.export()
def start(cmdline):
    """ Entry point """
    # Clean any invalid states
    win_enter()
    with ui.exception_to_errormsg():
        start_unite(state.parse_state(cmdline))


@vimh.export()
def cmdline_complete(arglead, cmdline, cursorpos):
    """ :h :command-completion-customlist """
    sources_and_options = list(option.format_options(option.default_options.keys())) + sources.__all__
    return filter(lambda x: x.startswith(arglead), sources_and_options)


@vimh.export()
def win_enter():
    """ We have to do this on WinEnter because vim.windows hasn't been updated
    yet on WinLeave
    """
    states.remove_invalid()


@vimh.export()
def vim_leave_pre():
    states.remove_some(states.get_states())


handlers = dict(
    # InsertEnter   = export()(on_insert_enter),
    # InsertLeave   = export()(on_insert_leave),
    # CursorHoldI   = export()(on_cursor_hold_i),
    # CursorMovedI  = export()(on_cursor_moved_i),
    # CursorMoved   = export()(on_cursor_moved),
    # CursorMovedI  = export()(on_cursor_moved),
    # BufHidden     = export()(on_buf_unload),
    # BufUnload     = export()(on_buf_unload),
    # BufWinEnter   = export()(on_bufwin_enter),
    # InsertCharPre = export()(on_insert_char_pre),
    # TextChanged   = export()(on_text_changed),
)


def set_buffer_autocommands(buff):
    vim.command('augroup plugin-pyunite')
    vim.command('autocmd! * <buffer={}>'.format(buff.number))
    for event, handler in handlers:
        vim.command('autocmd {} <buffer={}> call s:{}()'.format(
            event,
            buff.number,
            handler.func_name,
        ))
    vim.command('augroup END')


def set_buffer_options(buff):
    buff.options['bufhidden'] = 'wipe'
    buff.options['buflisted'] = False
    buff.options['buftype'] = 'nofile'
    buff.options['completefunc'] = ''
    buff.options['omnifunc'] = ''
    buff.options['iskeyword'] += ',-,+,\\,!,~'
    buff.options['matchpairs'] = re.sub('<:>,', '', buff.options['matchpairs'])
    buff.options['modeline'] = False
    buff.options['modifiable'] = False
    buff.options['readonly'] = False
    buff.options['swapfile'] = False
    buff.options['filetype'] = 'pyunite'


def set_buffer_mappings(buff):
    pass


def set_buffer_syntax(state):
    source = state.source
    contained = ''
    include_cmd = ''

    if source.syntaxes or source.include_syntax:
        contained += ' contains='

        if source.syntaxes:
            contained += source.name() + '_.*'

        if source.include_syntax:
            filetype = Path(source.include_syntax).stem.capitalize()
            contained += ',@' + filetype
            include_cmd = 'syntax include @' + filetype + ' ' + source.include_syntax

    magic = 'syntax region ' + source.name() + ' oneline keepend start=/^/ end=/$/' + contained

    vim.command('syntax clear')
    map(vim.command, [include_cmd] + source.syntaxes + source.highlights + [magic])
    vim.command('syntax sync minlines=1 maxlines=1')


def make_buffer_name(state):
    return '{}{} pyunite:{}:{} ({})'.format(
        '' if state.options['replace'] else '[NR] ',
        state.options['scope'][:3].upper(),
        state.source.name(),
        str(state.uid)[:7],
        len(state.source.candidates),
    )


def make_pyunite_buffer(state):
    with ui.restore(vim.current.buffer):
        buff = ui.make_buffer(make_buffer_name(state))
    set_buffer_options(buff)
    set_buffer_autocommands(buff)
    set_buffer_mappings(buff)
    ui.set_buffer_contents(buff, state.source.formatted_candidates())
    return buff


def set_window_options(window):
    if vimh.vhas('cursorbind'):
        window.options['cursorbind'] = False
    if vimh.vhas('conceal'):
        window.options['conceallevel'] = 3
        window.options['concealcursor'] = 'niv'
    if vimh.vexists('+cursorcolumn'):
        window.options['cursorcolumn'] = False
    if vimh.vexists('+colorcolumn'):
        window.options['colorcolumn'] = ''
    if vimh.vexists('+relativenumber'):
        window.options['relativenumber'] = False
    window.options['cursorline'] = False
    window.options['foldcolumn'] = 0
    window.options['foldenable'] = False
    window.options['list'] = False
    window.options['number'] = False
    window.options['scrollbind'] = False
    window.options['spell'] = False


def make_pyunite_window(state, autocmd=False):
    window = ui.make_window(
        direction=state.options['direction'],
        vsplit=state.options['vsplit'],
        size=state.options['size'],
        buffer_name=state.buff.name,
        autocmd=autocmd,
    )
    set_window_options(window)
    return window


def window_logic(state, old_state):
    """
    Window create/resize logic. The function name is not very good :(

      new_state  |   old_state   | same directions | same size |  action
    -------------|---------------|-----------------|-----------|-----------
      vertical   |    vertical   |      True       |   True    |  reuse
      vertical   |    vertical   |      True       |   False   |  resize
      vertical   |    vertical   |      False      |   True    |  close old; create
      vertical   |    vertical   |      False      |   False   |  close old; create
      vertical   |   horizontal  |      True       |   True    |  close old; create
      vertical   |   horizontal  |      True       |   False   |  close old; create
      vertical   |   horizontal  |      False      |   True    |  close old; create
      vertical   |   horizontal  |      False      |   False   |  close old; create
     horizontal  |    vertical   |      True       |   True    |  close old; create
     horizontal  |    vertical   |      True       |   False   |  close old; create
     horizontal  |    vertical   |      False      |   True    |  close old; create
     horizontal  |    vertical   |      False      |   False   |  close old; create
     horizontal  |   horizontal  |      True       |   True    |  reuse
     horizontal  |   horizontal  |      True       |   False   |  resize
     horizontal  |   horizontal  |      False      |   True    |  close old; create
     horizontal  |   horizontal  |      False      |   False   |  close old; create
    """
    old_window = vimh.window_with_buffer(old_state.buff) if old_state else None

    if not old_state or not old_window:
        window = make_pyunite_window(state, autocmd=True)

    elif ((state.options['vsplit'], state.options['direction']) ==
          (old_state.options['vsplit'], old_state.options['direction'])):
        ui.change_window(old_window, autocmd=True)
        ui.resize_window(state.options['size'] or old_state.options['size'], vsplit=state.options['vsplit'])
        window = old_window

    else:
        ui.change_window(old_window)
        # If bufhidden=wipe, buffer will dissapear when we close its window
        with ui.restore(vim.current.window), misc.scoped(state.buff.options, bufhidden='hide'):
            ui.quit_window()
        window = make_pyunite_window(state, autocmd=True)

    state.options['size'] = window.width if state.options['vsplit'] else window.height
    return window


def state_logic(state):
    """
    State create/replace/reuse logic. The function name is not very good :(

        state      |  other_state  | same source  | what to reuse from other_state
    ---------------|---------------|--------------|-------------------------------
       replace     |    replace    |    True      |  uid, buffer, source
       replace     |    replace    |    False     |  uid, buffer
       replace     |   no-replace  |    True      |  source
       replace     |   no-replace  |    False     |  nothing
      no-replace   |    replace    |    True      |  uid, buffer, source
      no-replace   |    replace    |    False     |  uid, buffer
      no-replace   |   no-replace  |    True      |  source
      no-replace   |   no-replace  |    False     |  nothing
    """
    # Only consider states which are in the same container
    in_same_container = filter(lambda s: s.container == state.container, states.get_states())

    other = iterator.find(
        lambda s: s.source == state.source and s.options['replace'] == True,
        in_same_container
    )

    if other:
        states.remove(other, wipeout_buffer=False)
        state.uid = other.uid
        state.buff = other.buff
        state.source = other.source
        return state, other

    other = iterator.find(
        lambda s: s.source != state.source and s.options['replace'] == True,
        in_same_container,
    )

    if other:
        states.remove(other, wipeout_buffer=False)
        state.uid = other.uid
        state.buff = other.buff
        state.source.populate_candidates()
        ui.set_buffer_contents(state.buff, state.source.formatted_candidates())
        return state, other

    other = iterator.find(lambda s: s.source == state.source, in_same_container)
    if other:
        state.source = other.source
    else:
        state.source.populate_candidates()
    return state, None


def start_unite(state):
    state, old_state = state_logic(state)
    # State is brand new. Have to create buffer for it
    if not state.buff:
        state.buff = make_pyunite_buffer(state)
    if state.options['close_on_empty'] and not len(state.source.candidates):
        return
    saved = vim.current.window
    window_logic(state, old_state)
    set_buffer_syntax(state)
    if not state.options['focus_on_open']:
        ui.change_window(saved, autocmd=True)
    states.add(state)
