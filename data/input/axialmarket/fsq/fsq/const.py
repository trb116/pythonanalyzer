# fsq -- a python library for manipulating and introspecting FSQ queues
# @author: Matthew Story <matt.story@axial.net>
#
# fsq/const.py -- provides constants convenience functions: const, set_const
#
#     fsq is all unicode internally, if you pass in strings,
#     they will be explicitly coerced to unicode.
#
#   NB: changes to environment following first import, will not
#       affect values potentially a bug to clean up later.
#
# This software is for POSIX compliant systems only.
import errno
import numbers

from . import constants as _c, FSQEnvError
from .internal import coerce_unicode

def const(const):
    '''Convenience wrapper to yield the value of a constant'''
    try:
        return getattr(_c, const)
    except AttributeError:
        raise FSQEnvError(errno.EINVAL, u'No such constant:'\
                               u' {0}'.format(const))
    except TypeError:
        raise TypeError(errno.EINVAL, u'const name must be a string or'\
                        u' unicode object, not:'\
                        u' {0}'.format(const.__class__.__name__))

def set_const(const, val):
    '''Convenience wrapper to reliably set the value of a constant from
       outside of package scope'''
    try:
        cur = getattr(_c, const)
    except AttributeError:
        raise FSQEnvError(errno.ENOENT, u'no such constant:'\
                          u' {0}'.format(const))
    except TypeError:
        raise TypeError(errno.EINVAL, u'const name must be a string or'\
                        u' unicode object, not:'\
                        u' {0}'.format(const.__class__.__name__))
    should_be = cur.__class__
    try:
        if not isinstance(val, should_be):
            if should_be is unicode or cur is None:
                val = coerce_unicode(val, _c.FSQ_CHARSET)
            elif should_be is int and const.endswith('MODE'):
                val = int(val, 8)
            elif isinstance(cur, numbers.Integral):
                val = int(val)
            else:
                should_be(val)
    except (TypeError, ValueError, ):
        raise FSQEnvError(errno.EINVAL, u'invalid type for constant {0},'\
                          u' should be {1}, not:'\
                          u' {2}'.format(const, should_be.__name__,
                                         val.__class__.__name__))
    setattr(_c, const, val)
    return val
