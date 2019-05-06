import vim
from functools import partial
from contextlib import contextmanager

from . import misc, exceptions


@contextmanager
def exception_to_errormsg():
    try:
        yield
    except exceptions.PyUniteWarning as e:
        warn(str(e))
    except exceptions.PyUniteError as e:
        error(str(e))
    except AssertionError as e:
        # It's better to provide a stack trace than nothing
        if not str(e):
            raise
        warn(str(e))


@contextmanager
def restore(vimobj, autocmd=False):
    """ Restore a vim object (tabpage, window, etc...) after inversion of
    control is done """
    saved = vimobj
    change_func = {
        type(vim.current.tabpage): change_tabpage,
        type(vim.current.window): change_window,
        type(vim.current.buffer): change_buffer,
    }[type(vimobj)]
    try:
        yield
    finally:
        if saved.valid:
            change_func(saved, autocmd)


@contextmanager
def highlight(higroup):
    """ Set highlight group for the duration of this context """
    vim.command('echohl ' + higroup)
    try:
        yield
    finally:
        vim.command('echohl None')


def echo(msg, high='Normal', store=False):
    with highlight(high):
        vim.command("echom '" + misc.escape_quote(msg) + "'")


warn = partial(echo, high='WarningMsg')
error = partial(echo, high='ErrorMsg')


def change_tabpage(tabpage, autocmd=False):
    vim.command('silent {} tabnext {}'.format('' if autocmd else 'noautocmd', tabpage.number))


def make_window(direction='', vsplit=False, size=0, buffer_name='', autocmd=False):
    vim.command('silent {} {} {}{} {}'.format(
        '' if autocmd else 'noautocmd',
        direction,
        str(size) if size > 0 else '',
        'vnew' if vsplit else 'new',
        misc.escape(' ', buffer_name),
    ))
    return vim.current.window


def change_window(window, autocmd=False):
    vim.command('silent {} {}wincmd w'.format('' if autocmd else 'noautocmd', window.number))


def resize_window(size, vsplit=False, autocmd=False):
    vim.command('silent {} {} resize {}'.format(
        '' if autocmd else 'noautocmd',
        'vertical' if vsplit else '',
        size
    ))


def quit_window(autocmd=False):
    vim.command('silent {} close!'.format('' if autocmd else 'noautocmd'))


def make_buffer(name, autocmd=False):
    with restore(vim.current.buffer):
        vim.command('silent {} edit {}'.format('' if autocmd else 'noautocmd', misc.escape(' ', name)))
        return vim.current.buffer


def change_buffer(buff, autocmd=False):
    vim.command('silent {} {}buffer'.format('' if autocmd else 'noautocmd', buff.number))


def wipeout_buffer(buff, autocmd=False):
    vim.command('silent {} bwipeout! {}'.format('' if autocmd else 'noautocmd', buff.number))


def set_buffer_contents(buff, contents):
    with misc.scoped(buff.options, modifiable=True):
        buff[:] = None
        buff.append(list(contents), 0)
