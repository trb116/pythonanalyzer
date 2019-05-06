# fsq -- a python library for manipulating and introspecting FSQ queues
# @author: Matthew Story <matt.story@axial.net>
#
# fsq/encode.py -- provides encoding functions: encode, decode
#
#     fsq is all unicode internally, if you pass in strings,
#     they will be explicitly coerced to unicode.
#
# This software is for POSIX compliant systems only.
import errno
import os

from . import FSQEncodeError, constants as _c
from .internal import coerce_unicode, delimiter_encodeseq

####### INTERNAL MODULE FUNCTIONS AND ATTRIBUTES #######
_ENCODED = (os.path.sep,)

####### EXPOSED METHODS #######
# we use a very lightweight ``percent'' encoding
def encode(arg, delimiter=None, encodeseq=None, encoded=tuple()):
    '''Encode a single argument for the file-system'''
    arg = coerce_unicode(arg, _c.FSQ_CHARSET)
    new_arg = sep = u''
    delimiter, encodeseq = delimiter_encodeseq(
        _c.FSQ_DELIMITER if delimiter is None else delimiter,
        _c.FSQ_ENCODE if encodeseq is None else encodeseq,
        _c.FSQ_CHARSET)

    # validate encoded tuple
    for enc in encoded:
        enc = coerce_unicode(enc, _c.FSQ_CHARSET)
        try:
            enc = enc.encode('ascii')
        except UnicodeEncodeError:
            raise FSQEncodeError(errno.EINVAL, u'invalid encoded value: {0}'\
                                 u' non-ascii'.format(enc))
    # char-wise encode walk
    for seq in arg:
        if seq == delimiter or seq == encodeseq or seq in _ENCODED + encoded:
            h_val = hex(ord(seq))
            # front-pad with zeroes
            if 3 == len(h_val):
                h_val = sep.join([h_val[:2], u'0', h_val[2:]])
            if 4 != len(h_val):
                raise FSQEncodeError(errno.EINVAL, u'invalid hex ({0}) for'\
                                     ' encode-target: {1}'.format(h_val, seq))
            seq = sep.join([encodeseq, h_val[2:]])

        new_arg = sep.join([new_arg, seq])

    return new_arg

def decode(arg, delimiter=None, encodeseq=None):
    '''Decode a single argument from the file-system'''
    arg = coerce_unicode(arg, _c.FSQ_CHARSET)
    new_arg = sep = u''
    delimiter, encodeseq = delimiter_encodeseq(
        _c.FSQ_DELIMITER if delimiter is None else delimiter,
        _c.FSQ_ENCODE if encodeseq is None else encodeseq,
        _c.FSQ_CHARSET)

    # char-wise decode walk -- minimally stateful
    encoding_trg = sep
    for c in arg:
        if len(encoding_trg):
            encoding_trg = sep.join([encoding_trg, c])
            if 4 !=  len(encoding_trg):
                continue
            try:
                c = chr(int(encoding_trg, 16))
            except ValueError:
                raise FSQEncodeError(errno.EINVAL, u'invalid decode'\
                                     u' target: {0}'.format(encoding_trg))
            c = coerce_unicode(c, _c.FSQ_CHARSET)
            encoding_trg = sep
        elif c == encodeseq:
            encoding_trg = u'0x'
            continue

        new_arg = sep.join([new_arg, c])

    # edge case, incomplete encoding at end of string
    if len(encoding_trg):
        raise FSQEncodeError(errno.EINVAL, u'truncated encoding at end of'
                             u' argument: {0}'.format(encoding_trg))

    return new_arg
