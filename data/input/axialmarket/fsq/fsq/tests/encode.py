from . import FSQTestCase
from .internal import normalize
from . import constants as _test_c

# FROM PAPA-BEAR IMPORT THE FOLLOWING
from .. import encode, decode, constants as _c, FSQCoerceError, FSQEncodeError

class TestEncodeDecode(FSQTestCase):
    def _cycle(self, arg, fsq_encode=None, fsq_delimiter=None, assert_eq=True,
               **kwargs):
        normalize()
        if fsq_encode is not None:
            _c.FSQ_ENCODE = fsq_encode
        if fsq_delimiter is not None:
            _c.FSQ_DELIMITER = fsq_delimiter
        encoded = encode(arg, **kwargs)
        if kwargs.has_key('encoded'):
            del kwargs['encoded']
        decoded = decode(encoded, **kwargs)
        if assert_eq:
            self.assertEquals(decoded, arg)
        return decoded

    def test_basic(self):
        for encodeseq, delimiter in ( _test_c.ORIG_ENCODE_DELIMITER,
                                    ( _test_c.ENCODE, _test_c.DELIMITER, )):
            for i in _test_c.NORMAL + ( _c.FSQ_DELIMITER.join(_test_c.NORMAL),
                                        _c.FSQ_ENCODE.join(_test_c.NORMAL),
                                        _c.FSQ_ENCODE.join([
                                            _test_c.NON_ASCII]*2), )\
                                    + _test_c.ILLEGAL_NAMES:
                # one set, then the other, then both
                self._cycle(i, fsq_encode=encodeseq)
                self._cycle(i, fsq_delimiter=delimiter)
                self._cycle(i, fsq_encode=encodeseq, fsq_delimiter=delimiter)
                # one passed, then the other, then both
                self._cycle(i, encodeseq=encodeseq)
                self._cycle(i, delimiter=delimiter)
                self._cycle(i, encodeseq=encodeseq, delimiter=delimiter)
                # test encoded kwarg for encode
                self._cycle(i, encoded=_test_c.ENCODED)
                self._cycle(i, encodeseq=encodeseq, encoded=_test_c.ENCODED)
                self._cycle(i, delimiter=delimiter, encoded=_test_c.ENCODED)
                self._cycle(i, encodeseq=encodeseq, delimiter=delimiter,
                            encoded=_test_c.ENCODED)
        # test coercion
        for i in _test_c.MODES:
            # int coerce
            self.assertEquals(unicode(i), self._cycle(i, assert_eq=False))
            # float coerce
            self.assertEquals(unicode(float(i)), self._cycle(float(i),
                              assert_eq=False))

    def test_badencode(self):
        # assert failure for bad encode char
        normalize()
        _c.FSQ_ENCODE = _test_c.ILLEGAL_ENCODE
        self.assertRaises(FSQEncodeError, encode, _test_c.NORMAL[0])
        normalize()
        self.assertRaises(FSQEncodeError, encode, _test_c.NORMAL[0],
                          encodeseq=_test_c.ILLEGAL_ENCODE)
        normalize()
        _c.FSQ_ENCODE = _test_c.ILLEGAL_NAME
        self.assertRaises(FSQCoerceError, encode, _test_c.NORMAL[0])
        normalize()
        self.assertRaises(FSQCoerceError, encode, _test_c.NORMAL[0],
                          encodeseq=_test_c.ILLEGAL_NAME)
        # assert failure for non coercable arg
        self.assertRaises(FSQCoerceError, encode, _test_c.ILLEGAL_NAME)

        normalize()
        # non-ascii encoded
        self.assertRaises(FSQEncodeError, encode, _test_c.NORMAL[0],
                          encoded=(_test_c.NON_ASCII,))
        normalize()
        # non-ascii encodeseq
        self.assertRaises(FSQEncodeError, encode, _test_c.NORMAL[0],
                          encodeseq=_test_c.NON_ASCII)
        normalize()
        # non-ascii delimiter
        self.assertRaises(FSQEncodeError, encode, _test_c.NORMAL[0],
                          delimiter=_test_c.NON_ASCII,)
        # delimiter and encodeseq set to be same
        normalize()
        self.assertRaises(FSQEncodeError, encode, _test_c.NORMAL[0],
                          delimiter=_c.FSQ_ENCODE)

    def test_baddecode(self):
        # assert failure for bad encode char
        normalize()
        _c.FSQ_ENCODE = _test_c.ILLEGAL_ENCODE
        self.assertRaises(FSQEncodeError, decode, _test_c.NORMAL[0])
        normalize()
        self.assertRaises(FSQEncodeError, decode, _test_c.NORMAL[0],
                          encodeseq=_test_c.ILLEGAL_ENCODE)
        normalize()
        _c.FSQ_ENCODE = _test_c.ILLEGAL_NAME
        self.assertRaises(FSQCoerceError, decode, _test_c.NORMAL[0])
        normalize()
        self.assertRaises(FSQCoerceError, decode, _test_c.NORMAL[0],
                          encodeseq=_test_c.ILLEGAL_NAME)
        # incomplete finishing seq
        self.assertRaises(FSQEncodeError, decode, _c.FSQ_DELIMITER.join([
            _test_c.NORMAL[0], _c.FSQ_ENCODE ]))

        # encoded non-ascii
        bad_val = u''.join([_c.FSQ_ENCODE, hex(ord(_test_c.NON_ASCII))])
        self.assertRaises(FSQEncodeError, decode, bad_val)

        # assert failure for non coercable arg
        self.assertRaises(FSQCoerceError, decode, _test_c.ILLEGAL_NAME)
