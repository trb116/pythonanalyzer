# fsq -- a python library for manipulating and introspecting FSQ queues
# @author: Matthew Story <matt.story@axial.net>
# @author: Jeff Rand <jeff.rand@axial.net>
#
# fsq/constants.py -- a place for constants.  per FSQ specification,
#   constants take their value from the calling program environment
#   (if available), and default to the the expected values.
#
#     fsq is all unicode internally, if you pass in strings,
#     they will be explicitly coerced to unicode.
#
#   NB: changes to environment following first import, will not
#       affect values potentially a bug to clean up later.
#
# TODO: make the defaults build-time configurable
# This software is for POSIX compliant systems only.
import os
import errno

from . import FSQEnvError
from .internal import coerce_unicode

# CONSTANTS WHICH ARE AFFECTED BY ENVIRONMENT
FSQ_CHARSET = os.environ.get("FSQ_CHARSET", u'utf8')
FSQ_CHARSET = coerce_unicode(FSQ_CHARSET, FSQ_CHARSET)
FSQ_DELIMITER = coerce_unicode(os.environ.get("FSQ_DELIMITER", u'_'),
                               FSQ_CHARSET)
FSQ_ENCODE = coerce_unicode(os.environ.get("FSQ_ENCODE", u'%'), FSQ_CHARSET)
FSQ_TIMEFMT = coerce_unicode(os.environ.get("FSQ_TIMEFMT", u'%Y%m%d%H%M%S'),
                             FSQ_CHARSET)
FSQ_QUEUE = coerce_unicode(os.environ.get("FSQ_QUEUE", u'queue'), FSQ_CHARSET)
FSQ_DONE = coerce_unicode(os.environ.get("FSQ_DONE", u'done'), FSQ_CHARSET)
FSQ_FAIL = coerce_unicode(os.environ.get("FSQ_FAIL", u'fail'), FSQ_CHARSET)
FSQ_TMP = coerce_unicode(os.environ.get("FSQ_TMP", u'tmp'), FSQ_CHARSET)
FSQ_DOWN = coerce_unicode(os.environ.get("FSQ_DOWN", u'down'), FSQ_CHARSET)
FSQ_TRIGGER = coerce_unicode(os.environ.get("FSQ_TRIGGER", u'trigger-s'),
                             FSQ_CHARSET)
FSQ_ROOT = coerce_unicode(os.environ.get("FSQ_ROOT", u'/var/fsq'),
                          FSQ_CHARSET)
FSQ_HOSTS = coerce_unicode(os.environ.get("FSQ_HOSTS", u'hosts'),
                          FSQ_CHARSET)
FSQ_HOSTS_TRIGGER = coerce_unicode(os.environ.get("FSQ_HOSTS_TRIGGER",
                                   u'hosts-trigger-s'), FSQ_CHARSET)

# these 2 default to None, as gid/uid may change in due course
# when using these 2, default to os.getgid(), os.getuid()
# should be relatively few places
FSQ_ITEM_GROUP = coerce_unicode(os.environ.get("FSQ_ITEM_GROUP", u''),
                                FSQ_CHARSET) or None
FSQ_ITEM_USER = coerce_unicode(os.environ.get("FSQ_ITEM_USER", u''),
                               FSQ_CHARSET) or None
FSQ_QUEUE_GROUP = coerce_unicode(os.environ.get("FSQ_QUEUE_GROUP", u''),
                                 FSQ_CHARSET) or None
FSQ_QUEUE_USER = coerce_unicode(os.environ.get("FSQ_QUEUE_USER", u''),
                                FSQ_CHARSET) or None

# directory where fsq libraries for executables live
FSQ_EXEC_DIR = coerce_unicode(os.environ.get("FSQ_EXEC_DIR", u''),
                              FSQ_CHARSET) or None

try:
    # octal mode representation -- e.g. 700, 0700, etc.
    FSQ_ITEM_MODE = int(coerce_unicode(os.environ.get("FSQ_ITEM_MODE",
                        u'00640'), FSQ_CHARSET), 8)
    FSQ_QUEUE_MODE = int(coerce_unicode(os.environ.get("FSQ_QUEUE_MODE",
                         u'02770'), FSQ_CHARSET), 8)
    # failure cases
    FSQ_FAIL_TMP = int(os.environ.get("FSQ_FAIL_TMP", 111))
    FSQ_FAIL_PERM = int(os.environ.get("FSQ_FAIL_PERM", 100))
    # success
    FSQ_SUCCESS = int(os.environ.get("FSQ_SUCCESS", 0))
    # use triggers or not
    FSQ_USE_TRIGGER = int(os.environ.get("FSQ_USE_TRIGGER", 0))
    # get/respect exclusive locks on queue items
    FSQ_LOCK = int(os.environ.get("FSQ_LOCK", 1))
    # max tries before tmp fails become permanant -- 0 is infinite
    FSQ_MAX_TRIES = int(os.environ.get("FSQ_MAX_TRIES", 1))
    # time-to-live (in seconds) for any queue item -- 0 is infinite
    FSQ_TTL = int(os.environ.get("FSQ_TTL", 0))
except ValueError, e:
    raise FSQEnvError(errno.EINVAL, e.message)
