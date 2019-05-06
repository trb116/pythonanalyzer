"""Test digest API"""
from __future__ import absolute_import, division, print_function
from itertools import islice

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from tls.c import api


class DigestTests(object):

    data_short = b'abc'
    data_long = b'abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq'

    def setUp(self):
        self.ctx = api.EVP_MD_CTX_create()
        api.EVP_DigestInit_ex(self.ctx, self.digest, api.NULL)
        self.ctx_two = api.EVP_MD_CTX_create()
        api.EVP_DigestInit_ex(self.ctx_two, self.digest, api.NULL)

    def tearDown(self):
        api.EVP_MD_CTX_destroy(self.ctx)
        api.EVP_MD_CTX_destroy(self.ctx_two)

    def test_short(self):
        data = api.new('char[]', self.data_short)
        buf = api.new('unsigned char[]', api.EVP_MAX_MD_SIZE)
        size = api.new('unsigned int*')
        api.EVP_DigestUpdate(self.ctx, api.cast('void*', data), len(self.data_short))
        api.EVP_DigestFinal_ex(self.ctx, buf, size)
        hash_value = b''.join('{0:02x}'.format(v).encode() for v in islice(buf, size[0]))
        self.assertEqual(hash_value, self.hash_short)

    def test_long(self):
        data = api.new('char[]', self.data_long)
        buf = api.new('unsigned char[]', api.EVP_MAX_MD_SIZE)
        size = api.new('unsigned int*')
        api.EVP_DigestUpdate(self.ctx, api.cast('void*', data), len(self.data_long))
        api.EVP_DigestFinal_ex(self.ctx, buf, size)
        hash_value = b''.join('{0:02x}'.format(v).encode() for v in islice(buf, size[0]))
        self.assertEqual(hash_value, self.hash_long)

    def test_copy(self):
        data = api.new('char[]', self.data_short)
        buf = api.new('unsigned char[]', api.EVP_MAX_MD_SIZE)
        size = api.new('unsigned int*')
        api.EVP_DigestUpdate(self.ctx, api.cast('void*', data), len(self.data_short))

        api.EVP_MD_CTX_copy_ex(self.ctx_two, self.ctx)
        api.EVP_DigestFinal_ex(self.ctx_two, buf, size)
        hash_value = b''.join('{0:02x}'.format(v).encode() for v in islice(buf, size[0]))
        self.assertEqual(hash_value, self.hash_short)

        data = api.new('char[]', self.data_long[len(self.data_short):])
        api.EVP_DigestUpdate(self.ctx, api.cast('void*', data), len(data) - 1)
        api.EVP_DigestFinal_ex(self.ctx, buf, size)
        hash_value = b''.join('{0:02x}'.format(v).encode() for v in islice(buf, size[0]))
        self.assertEqual(hash_value, self.hash_long)


class TestSHA1(DigestTests, unittest.TestCase):
    "Test data source from http://www.nsrl.nist.gov/testdata/"

    hash_short = b"a9993e364706816aba3e25717850c26c9cd0d89d"
    hash_long = b"84983e441c3bd26ebaae4aa1f95129e5e54670f1"

    @property
    def digest(cls):
        return api.EVP_sha1()


class TestMD5(DigestTests, unittest.TestCase):
    "Test data source from http://www.nsrl.nist.gov/testdata/"

    hash_short = b"900150983cd24fb0d6963f7d28e17f72"
    hash_long = b"8215ef0796a20bcaaae116d3876c664a"

    @property
    def digest(self):
        return api.EVP_md5()


class TestSHA256(DigestTests, unittest.TestCase):
    "Test data source from http://www.nsrl.nist.gov/testdata/"

    hash_short = b"ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    hash_long = b"248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1"

    @property
    def digest(self):
        return api.EVP_sha256()


class TestEVP(unittest.TestCase):

    def test_init(self):
        ctx = api.new('EVP_MD_CTX*')
        self.assertTrue(ctx)
        api.EVP_MD_CTX_init(ctx)
        api.EVP_MD_CTX_cleanup(ctx)

    def test_create(self):
        ctx = api.EVP_MD_CTX_create()
        self.assertTrue(ctx)
        api.EVP_MD_CTX_destroy(ctx)

    def _test_md_func(self, name, nid_name=None):
        nid_name = 'NID_' + name.lower() if nid_name is None else nid_name
        getter = getattr(api, 'EVP_{0}'.format(name.lower()))
        num = getattr(api, nid_name)
        md = getter()
        self.assertTrue(md)
        self.assertEqual(api.EVP_MD_type(md), num)

    def test_md_null_func(self):
        self._test_md_func('md_null', 'NID_undef')

    @unittest.skip('unpredictable support')
    def test_dsa_func(self):
        self._test_md_func('dsa_sha', 'DSS')

    @unittest.skip('unpredictable support')
    def test_dsa1_func(self):
        self._test_md_func('dsa_sha1', 'NID_dsaWithSHA1')

    def test_dss_func(self):
        self._test_md_func('dss', 'NID_dsaWithSHA')

    @unittest.skip('unpredictable support')
    def test_dss1_func(self):
        self._test_md_func('dss1', 'NID_dsaWithSHA1')

    def test_ecdsa_func(self):
        self._test_md_func('ecdsa', 'NID_ecdsa_with_SHA1')

    @unittest.skip('unpredictable support')
    def test_md2_func(self):
        self._test_md_func('md2')

    def test_md4_func(self):
        self._test_md_func('md4')

    def test_md5_func(self):
        self._test_md_func('md5')

    @unittest.skip('unpredictable support')
    def test_mdc2_func(self):
        self._test_md_func('mdc2')

    def test_ripemd160_func(self):
        self._test_md_func('ripemd160')

    def test_sha_func(self):
        self._test_md_func('sha')

    def test_sha1_func(self):
        self._test_md_func('sha1')

    def test_sha224_func(self):
        self._test_md_func('sha224')

    def test_sha256_func(self):
        self._test_md_func('sha256')

    def test_sha384_func(self):
        self._test_md_func('sha384')

    def test_sha512_func(self):
        self._test_md_func('sha512')

    def _test_md_name(self, name, nid_name=None):
        if nid_name is None:
            nid_name = b'NID_' + name.lower()
        md_name = name
        num = getattr(api, nid_name.decode())
        md = api.EVP_get_digestbyname(md_name)
        self.assertTrue(md)
        self.assertEqual(api.EVP_MD_type(md), num)

    def test_dsa_name(self):
        self._test_md_name(b'DSA', b'NID_dsa')

    def test_dsa_sha_name(self):
        self._test_md_name(b'DSA-SHA', b'NID_dsaWithSHA')

    @unittest.skip('unpredictable support')
    def test_dsa_sha1_name(self):
        self._test_md_name(b'DSA-SHA1', b'NID_dsaWithSHA1')

    def test_ecdsa_name(self):
        self._test_md_name(b'ecdsa-with-SHA1', b'NID_ecdsa_with_SHA1')

    @unittest.skip('unpredictable support')
    def test_md2_name(self):
        self._test_md_name(b'MD2')

    def test_md4_name(self):
        self._test_md_name(b'MD4')

    def test_md5_name(self):
        self._test_md_name(b'MD5')

    @unittest.skip('unpredictable support')
    def test_mdc2_name(self):
        self._test_md_name(b'MDC2')

    def test_ripemd160_name(self):
        self._test_md_name(b'RIPEMD160')

    def test_sha_name(self):
        self._test_md_name(b'SHA')

    def test_sha1_name(self):
        self._test_md_name(b'SHA1')

    def test_sha224_name(self):
        self._test_md_name(b'SHA224')

    def test_sha256_name(self):
        self._test_md_name(b'SHA256')

    def test_sha384_name(self):
        self._test_md_name(b'SHA384')

    def test_sha512_name(self):
        self._test_md_name(b'SHA512')

    def _test_md_nid(self, nid, name):
        self.assertEqual(name, api.string(api.OBJ_nid2sn(nid)))
        md = api.EVP_get_digestbynid(nid)
        self.assertTrue(md)

    @unittest.skip('unpredictable support')
    def test_md2_nid(self):
        self._test_md_nid(api.NID_md2, b'MD2')

    def test_md4_nid(self):
        self._test_md_nid(api.NID_md4, b'MD4')

    def test_md5_nid(self):
        self._test_md_nid(api.NID_md5, b'MD5')

    @unittest.skip('unpredictable support')
    def test_mdc2_nid(self):
        self._test_md_nid(api.NID_mdc2, b'MDC2')

    def test_ripemd160_nid(self):
        self._test_md_nid(api.NID_ripemd160, b'RIPEMD160')

    def test_sha_nid(self):
        self._test_md_nid(api.NID_sha, b'SHA')

    def test_sha1_nid(self):
        self._test_md_nid(api.NID_sha1, b'SHA1')

    def test_sha224_nid(self):
        self._test_md_nid(api.NID_sha224, b'SHA224')

    def test_sha256_nid(self):
        self._test_md_nid(api.NID_sha256, b'SHA256')

    def test_sha384_nid(self):
        self._test_md_nid(api.NID_sha384, b'SHA384')

    def test_sha512_nid(self):
        self._test_md_nid(api.NID_sha512, b'SHA512')
