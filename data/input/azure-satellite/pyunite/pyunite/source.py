import re
from importlib import import_module
from abc import ABCMeta, abstractmethod

from .exceptions import *


class Source(object):
    """ Plugin authors can extend this object to define a source """

    __metaclass__ = ABCMeta

    include_syntax = ''

    syntaxes = []

    highlights = []

    candidates = []

    def __init__(self, args):
        self.args = args

    def __eq__(self, other):
        return (self.name(), self.args) == (other.name(), other.args)

    @classmethod
    def name(cls):
        return cls.__name__.lower()

    @abstractmethod
    def populate_candidates(self):
        pass

    def formatted_candidates(self):
        return self.candidates


def parse_source(string):
    colons_with_no_backslashes = r'(?<!\\):'
    splits = re.split(colons_with_no_backslashes, string)
    name = splits[0]
    args = splits[1:]
    try:
        cls = name.capitalize()
        return import_module('pyunite.sources.' + name).__dict__[cls](args)
    except ImportError:
        error = 'Source "{}" is not recognized'.format(name)
        raise PyUniteError(error)
    except KeyError:
        error = 'Expected {} for class name in source {}'.format(cls, name)
        raise PyUniteError(error)
