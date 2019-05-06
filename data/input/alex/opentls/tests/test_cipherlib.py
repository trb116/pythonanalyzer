"""Test Python cipherlib API module"""
from __future__ import absolute_import, division, print_function
import math
import mock

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from tls import cipherlib
from tls.c import api


if hasattr(str, 'decode'):
    int2byte = chr
else:
    int2byte = lambda i: bytes((i,))


class TestAlgorithms(unittest.TestCase):

    def test_guaranteed(self):
        self.assertEqual(set(), cipherlib.algorithms_guaranteed)

    def test_available(self):
        self.assertGreater(len(cipherlib.algorithms_available), 0)
        self.assertIn(b'AES-128-CBC', cipherlib.algorithms_available)


class CipherObject(object):

    def setUp(self):
        self.cipher = cipherlib.Cipher(self.ENCRYPT, self.ALGORITHM, self.DIGEST)

    def tearDown(self):
        if hasattr(self, 'cipher'):
            del self.cipher

    def test_algorithm(self):
        self.assertEqual(self.ALGORITHM, self.cipher.algorithm)

    def test_digest(self):
        self.assertEqual(self.DIGEST, self.cipher.digest)

    def test_digest_size(self):
        self.assertEqual(self.DIGEST_SIZE, self.cipher.digest_size)

    def test_block_size(self):
        self.assertEqual(self.LEN_BLOCK, self.cipher.block_size)

    def test_ivector_len(self):
        self.assertEqual(self.LEN_IV, self.cipher.ivector_len)

    def test_key_len(self):
        self.assertEqual(self.LEN_KEY, self.cipher.key_len)

    def test_decrypting(self):
        self.assertNotEqual(self.ENCRYPT, self.cipher.decrypting)

    def test_encrypting(self):
        self.assertEqual(self.ENCRYPT, self.cipher.encrypting)

    def test_mode(self):
        self.assertEqual(self.MODE, self.cipher.mode)

    def test_name(self):
        self.assertEqual(self.ALGORITHM, self.cipher.name)

    def test_invalid_name(self):
        self.assertRaises(ValueError, cipherlib.Cipher, self.ENCRYPT, b'UNDEF')

    def test_initialised(self):
        self.cipher.initialise(self.KEY, self.IVECTOR)
        self.assertTrue(self.cipher.is_initialised)

    def test_initialise_invalid_key(self):
        self.assertRaises(ValueError, self.cipher.initialise,
                self.KEY + b'\FF', self.IVECTOR)

    def test_initialise_invalid_ivector(self):
        self.assertRaises(ValueError, self.cipher.initialise,
                self.KEY, self.IVECTOR + b'\FF')

    def test_update(self):
        self.cipher.initialise(self.KEY, self.IVECTOR)
        self.cipher.update(b'\x00' * self.LEN_BLOCK)

    def test_update_invalid(self):
        self.assertRaises(ValueError, self.cipher.update, b'\x00' * self.LEN_BLOCK)

    def test_finish(self):
        self.cipher.initialise(self.KEY, self.IVECTOR)
        self.cipher.finish()

    def test_ciphertext(self):
        if not self.ENCRYPT:
            return
        self.cipher.initialise(self.KEY, self.IVECTOR)
        self.cipher.update(b'\x00' * self.LEN_BLOCK)
        self.cipher.finish()
        ciphertext = self.cipher.ciphertext()
        length = math.ceil(float(self.LEN_BLOCK + self.cipher.digest_size + 1)
                / self.LEN_BLOCK) * self.LEN_BLOCK
        self.assertEqual(len(ciphertext), length)

    def test_ciphertext_invalid(self):
        if self.ENCRYPT:
            return
        self.cipher.initialise(self.KEY, self.IVECTOR)
        self.cipher.update(b'\x00' * self.LEN_BLOCK)
        self.cipher.finish()
        self.assertRaises(ValueError, self.cipher.ciphertext)

#   def test_plaintext(self):
#       if self.ENCRYPT:
#           return
#       self.cipher.initialise(self.KEY, self.IVECTOR)
#       self.cipher.update('\x00' * self.LEN_BLOCK)
#       self.cipher.finish()
#       plaintext = self.cipher.plaintext()
#       self.assertEqual(len(plaintext), self.LEN_BLOCK)

    def test_plaintext_invalid(self):
        if not self.ENCRYPT:
            return
        self.cipher.initialise(self.KEY, self.IVECTOR)
        self.cipher.update(b'\x00' * self.LEN_BLOCK)
        self.cipher.finish()
        self.assertRaises(ValueError, self.cipher.plaintext)

    def test_weakref_bio(self):
        BIO_free_all_cleanup = api.BIO_free_all
        with mock.patch('tls.c.api.BIO_free_all') as cleanup_mock:
            cleanup_mock.side_effect = BIO_free_all_cleanup
            del self.cipher
            self.assertEqual(cleanup_mock.call_count, 1)


class TestAesEncryptObject(CipherObject, unittest.TestCase):

    ALGORITHM = b'AES-128-CBC'
    DIGEST = b'SHA1'
    DIGEST_SIZE = 20
    ENCRYPT = True
    IVECTOR = b'\x00' * 16
    KEY = b'\x00' * 16
    LEN_BLOCK = 16
    LEN_IV = 16
    LEN_KEY = 16
    MODE = cipherlib.EVP_CIPH_CBC_MODE

    def test_key_len_set(self):
        def change_key_len(length):
            self.cipher.key_len = length
        self.assertRaises(ValueError, change_key_len, 8)


class TestRc4DecryptObject(CipherObject, unittest.TestCase):

    ALGORITHM = b'RC4'
    DIGEST = b'MD5'
    DIGEST_SIZE = 16
    ENCRYPT = False
    IVECTOR = b''
    KEY = b'\x00' * 16
    LEN_BLOCK = 1
    LEN_IV = 0
    LEN_KEY = 16
    MODE = cipherlib.EVP_CIPH_STREAM_CIPHER

    def test_key_len_set(self):
        self.cipher_key_len = 8
        # self.assertEqual(8, self.cipher.key_len)


class TestDesEncryptObject(CipherObject, unittest.TestCase):

    ALGORITHM = b'DES-ECB'
    DIGEST = None
    DIGEST_SIZE = 0
    ENCRYPT = True
    IVECTOR = b''
    KEY = b'\x00' * 8
    LEN_BLOCK = 8
    LEN_IV = 0
    LEN_KEY = 8
    MODE = cipherlib.EVP_CIPH_ECB_MODE

    def test_key_len_set(self):
        def change_key_len(length):
            self.cipher.key_len = length
        self.assertRaises(ValueError, change_key_len, 16)


class CipherTests(object):

    @staticmethod
    def hexstr_to_bytestr(hexstr):
        chars = []
        for pos in range(0, len(hexstr), 2):
            chars.append(int(hexstr[pos:pos + 2], 16))
        return b"".join(int2byte(c) for c in chars)

    @classmethod
    def setUpClass(self):
        self.key = self.hexstr_to_bytestr(self.key)
        if self.iv is not None:
            self.iv = self.hexstr_to_bytestr(self.iv)
        self.plaintext = self.hexstr_to_bytestr(self.plaintext)
        self.ciphertext = self.hexstr_to_bytestr(self.ciphertext)

    def _encrypt(self):
        cipher = cipherlib.Cipher(True, self.algorithm)
        cipher.initialise(self.key, self.iv)
        cipher.update(self.plaintext)
        cipher.finish()
        return cipher.ciphertext()

    def _decrypt(self, data):
        cipher = cipherlib.Cipher(False, self.algorithm)
        cipher.initialise(self.key, self.iv)
        cipher.update(data)
        cipher.finish()
        return cipher.plaintext()

    def test_encrypt_decrypt(self):
        result = self._encrypt()
        self.assertEqual(result[:len(self.ciphertext)], self.ciphertext)
        result = self._decrypt(result)
        self.assertEqual(result[:len(self.plaintext)], self.plaintext)

    def test_bitflip_data_decrypt(self):
        result = self._encrypt()
        result = int2byte(ord(result[:1]) ^ 0x80) + result[1:]
        self.assertRaises(ValueError, self._decrypt, result)

    def test_bitflip_hmac_decrypt(self):
        result = self._encrypt()
        pos = len(self.ciphertext)
        result = (result[:pos]
                + int2byte(ord(result[pos:pos + 1]) ^ 0x80)
                + result[pos + 1:])
        self.assertRaises(ValueError, self._decrypt, result)

    def test_bitflip_padding_decrypt(self):
        result = self._encrypt()
        result = result[:-1] + int2byte(ord(result[-1:]) ^ 0x01)
        self.assertRaises(ValueError, self._decrypt, result)

    def test_trunc_data_decrypt(self):
        result = self._encrypt()
        result = result[1:]
        self.assertRaises(ValueError, self._decrypt, result)

    def test_trunc_hmac_decrypt(self):
        result = self._encrypt()
        pos = len(self.ciphertext)
        result = result[:pos] + result[pos + 1:]
        self.assertRaises(ValueError, self._decrypt, result)

    def test_trunc_padding_decrypt(self):
        result = self._encrypt()
        result = result[:-1]
        self.assertRaises(ValueError, self._decrypt, result)


class Test_AES_ECB_128_v1(CipherTests, unittest.TestCase):

    algorithm = b"AES-128-ECB"
    key = b"2b7e151628aed2a6abf7158809cf4f3c"
    iv = None
    plaintext = b"6bc1bee22e409f96e93d7e117393172a"
    ciphertext = b"3ad77bb40d7a3660a89ecaf32466ef97"


class Test_AES_ECB_128_v2(CipherTests, unittest.TestCase):

    algorithm = b"AES-128-ECB"
    key = b"2b7e151628aed2a6abf7158809cf4f3c"
    iv = None
    plaintext = b"ae2d8a571e03ac9c9eb76fac45af8e51"
    ciphertext = b"f5d3d58503b9699de785895a96fdbaaf"


class Test_AES_ECB_128_v3(CipherTests, unittest.TestCase):

    algorithm = b"AES-128-ECB"
    key = b"2b7e151628aed2a6abf7158809cf4f3c"
    iv = None
    plaintext = b"30c81c46a35ce411e5fbc1191a0a52ef"
    ciphertext = b"43b1cd7f598ece23881b00e3ed030688"


class Test_AES_ECB_128_v4(CipherTests, unittest.TestCase):

    algorithm = b"AES-128-ECB"
    key = b"2b7e151628aed2a6abf7158809cf4f3c"
    iv = None
    plaintext = b"f69f2445df4f9b17ad2b417be66c3710"
    ciphertext = b"7b0c785e27e8ad3f8223207104725dd4"


class Test_AES_ECB_192_v1(CipherTests, unittest.TestCase):

    algorithm = b"AES-192-ECB"
    key = b"8e73b0f7da0e6452c810f32b809079e562f8ead2522c6b7b"
    iv = None
    plaintext = b"6bc1bee22e409f96e93d7e117393172a"
    ciphertext = b"bd334f1d6e45f25ff712a214571fa5cc"


class Test_AES_ECB_192_v2(CipherTests, unittest.TestCase):

    algorithm = b"AES-192-ECB"
    key = b"8e73b0f7da0e6452c810f32b809079e562f8ead2522c6b7b"
    iv = None
    plaintext = b"ae2d8a571e03ac9c9eb76fac45af8e51"
    ciphertext = b"974104846d0ad3ad7734ecb3ecee4eef"


class Test_AES_ECB_192_v3(CipherTests, unittest.TestCase):

    algorithm = b"AES-192-ECB"
    key = b"8e73b0f7da0e6452c810f32b809079e562f8ead2522c6b7b"
    iv = None
    plaintext = b"30c81c46a35ce411e5fbc1191a0a52ef"
    ciphertext = b"ef7afd2270e2e60adce0ba2face6444e"


class Test_AES_ECB_192_v4(CipherTests, unittest.TestCase):

    algorithm = b"AES-192-ECB"
    key = b"8e73b0f7da0e6452c810f32b809079e562f8ead2522c6b7b"
    iv = None
    plaintext = b"f69f2445df4f9b17ad2b417be66c3710"
    ciphertext = b"9a4b41ba738d6c72fb16691603c18e0e"


class Test_AES_ECB_256_v1(CipherTests, unittest.TestCase):

    algorithm = b"AES-256-ECB"
    key = b"603deb1015ca71be2b73aef0857d77811f352c073b6108d72d9810a30914dff4"
    iv = None
    plaintext = b"6bc1bee22e409f96e93d7e117393172a"
    ciphertext = b"f3eed1bdb5d2a03c064b5a7e3db181f8"


class Test_AES_ECB_256_v2(CipherTests, unittest.TestCase):

    algorithm = b"AES-256-ECB"
    key = b"603deb1015ca71be2b73aef0857d77811f352c073b6108d72d9810a30914dff4"
    iv = None
    plaintext = b"ae2d8a571e03ac9c9eb76fac45af8e51"
    ciphertext = b"591ccb10d410ed26dc5ba74a31362870"


class Test_AES_ECB_256_v3(CipherTests, unittest.TestCase):

    algorithm = b"AES-256-ECB"
    key = b"603deb1015ca71be2b73aef0857d77811f352c073b6108d72d9810a30914dff4"
    iv = None
    plaintext = b"30c81c46a35ce411e5fbc1191a0a52ef"
    ciphertext = b"b6ed21b99ca6f4f9f153e7b1beafed1d"


class Test_AES_ECB_256_v4(CipherTests, unittest.TestCase):

    algorithm = b"AES-256-ECB"
    key = b"603deb1015ca71be2b73aef0857d77811f352c073b6108d72d9810a30914dff4"
    iv = None
    plaintext = b"f69f2445df4f9b17ad2b417be66c3710"
    ciphertext = b"23304b7a39f9f3ff067d8d8f9e24ecc7"


class Test_AES_CBC_128_v1(CipherTests, unittest.TestCase):

    algorithm = b"AES-128-CBC"
    key = b"2b7e151628aed2a6abf7158809cf4f3c"
    iv = b"000102030405060708090A0B0C0D0E0F"
    plaintext = b"6bc1bee22e409f96e93d7e117393172a"
    ciphertext = b"7649abac8119b246cee98e9b12e9197d"


class Test_AES_CBC_128_v2(CipherTests, unittest.TestCase):

    algorithm = b"AES-128-CBC"
    key = b"2b7e151628aed2a6abf7158809cf4f3c"
    iv = b"7649ABAC8119B246CEE98E9B12E9197D"
    plaintext = b"ae2d8a571e03ac9c9eb76fac45af8e51"
    ciphertext = b"5086cb9b507219ee95db113a917678b2"


class Test_AES_CBC_128_v3(CipherTests, unittest.TestCase):

    algorithm = b"AES-128-CBC"
    key = b"2b7e151628aed2a6abf7158809cf4f3c"
    iv = b"5086CB9B507219EE95DB113A917678B2"
    plaintext = b"30c81c46a35ce411e5fbc1191a0a52ef"
    ciphertext = b"73bed6b8e3c1743b7116e69e22229516"


class Test_AES_CBC_128_v4(CipherTests, unittest.TestCase):

    algorithm = b"AES-128-CBC"
    key = b"2b7e151628aed2a6abf7158809cf4f3c"
    iv = b"73BED6B8E3C1743B7116E69E22229516"
    plaintext = b"f69f2445df4f9b17ad2b417be66c3710"
    ciphertext = b"3ff1caa1681fac09120eca307586e1a7"


class Test_AES_CBC_192_v1(CipherTests, unittest.TestCase):

    algorithm = b"AES-192-CBC"
    key = b"8e73b0f7da0e6452c810f32b809079e562f8ead2522c6b7b"
    iv = b"000102030405060708090A0B0C0D0E0F"
    plaintext = b"6bc1bee22e409f96e93d7e117393172a"
    ciphertext = b"4f021db243bc633d7178183a9fa071e8"


class Test_AES_CBC_192_v2(CipherTests, unittest.TestCase):

    algorithm = b"AES-192-CBC"
    key = b"8e73b0f7da0e6452c810f32b809079e562f8ead2522c6b7b"
    iv = b"4F021DB243BC633D7178183A9FA071E8"
    plaintext = b"ae2d8a571e03ac9c9eb76fac45af8e51"
    ciphertext = b"b4d9ada9ad7dedf4e5e738763f69145a"


class Test_AES_CBC_192_v3(CipherTests, unittest.TestCase):

    algorithm = b"AES-192-CBC"
    key = b"8e73b0f7da0e6452c810f32b809079e562f8ead2522c6b7b"
    iv = b"B4D9ADA9AD7DEDF4E5E738763F69145A"
    plaintext = b"30c81c46a35ce411e5fbc1191a0a52ef"
    ciphertext = b"571b242012fb7ae07fa9baac3df102e0"


class Test_AES_CBC_192_v4(CipherTests, unittest.TestCase):

    algorithm = b"AES-192-CBC"
    key = b"8e73b0f7da0e6452c810f32b809079e562f8ead2522c6b7b"
    iv = b"571B242012FB7AE07FA9BAAC3DF102E0"
    plaintext = b"f69f2445df4f9b17ad2b417be66c3710"
    ciphertext = b"08b0e27988598881d920a9e64f5615cd"


class Test_AES_CBC_256_v1(CipherTests, unittest.TestCase):

    algorithm = b"AES-256-CBC"
    key = b"603deb1015ca71be2b73aef0857d77811f352c073b6108d72d9810a30914dff4"
    iv = b"000102030405060708090A0B0C0D0E0F"
    plaintext = b"6bc1bee22e409f96e93d7e117393172a"
    ciphertext = b"f58c4c04d6e5f1ba779eabfb5f7bfbd6"


class Test_AES_CBC_256_v2(CipherTests, unittest.TestCase):

    algorithm = b"AES-256-CBC"
    key = b"603deb1015ca71be2b73aef0857d77811f352c073b6108d72d9810a30914dff4"
    iv = b"F58C4C04D6E5F1BA779EABFB5F7BFBD6"
    plaintext = b"ae2d8a571e03ac9c9eb76fac45af8e51"
    ciphertext = b"9cfc4e967edb808d679f777bc6702c7d"


class Test_AES_CBC_256_v3(CipherTests, unittest.TestCase):

    algorithm = b"AES-256-CBC"
    key = b"603deb1015ca71be2b73aef0857d77811f352c073b6108d72d9810a30914dff4"
    iv = b"9CFC4E967EDB808D679F777BC6702C7D"
    plaintext = b"30c81c46a35ce411e5fbc1191a0a52ef"
    ciphertext = b"39f23369a9d9bacfa530e26304231461"


class Test_AES_CBC_256_v4(CipherTests, unittest.TestCase):

    algorithm = b"AES-256-CBC"
    key = b"603deb1015ca71be2b73aef0857d77811f352c073b6108d72d9810a30914dff4"
    iv = b"39F23369A9D9BACFA530E26304231461"
    plaintext = b"f69f2445df4f9b17ad2b417be66c3710"
    ciphertext = b"b2eb05e2c39be9fcda6c19078c6a9d1b"


class Test_AES_CFB_128_v1(CipherTests, unittest.TestCase):

    algorithm = b"AES-128-CFB"
    key = b"2b7e151628aed2a6abf7158809cf4f3c"
    iv = b"000102030405060708090a0b0c0d0e0f"
    plaintext = b"6bc1bee22e409f96e93d7e117393172a"
    ciphertext = b"3b3fd92eb72dad20333449f8e83cfb4a"


class Test_AES_CFB_128_v2(CipherTests, unittest.TestCase):

    algorithm = b"AES-128-CFB"
    key = b"2b7e151628aed2a6abf7158809cf4f3c"
    iv = b"3B3FD92EB72DAD20333449F8E83CFB4A"
    plaintext = b"ae2d8a571e03ac9c9eb76fac45af8e51"
    ciphertext = b"c8a64537a0b3a93fcde3cdad9f1ce58b"


class Test_AES_CFB_128_v3(CipherTests, unittest.TestCase):

    algorithm = b"AES-128-CFB"
    key = b"2b7e151628aed2a6abf7158809cf4f3c"
    iv = b"C8A64537A0B3A93FCDE3CDAD9F1CE58B"
    plaintext = b"30c81c46a35ce411e5fbc1191a0a52ef"
    ciphertext = b"26751f67a3cbb140b1808cf187a4f4df"


class Test_AES_CFB_128_v4(CipherTests, unittest.TestCase):

    algorithm = b"AES-128-CFB"
    key = b"2b7e151628aed2a6abf7158809cf4f3c"
    iv = b"26751F67A3CBB140B1808CF187A4F4DF"
    plaintext = b"f69f2445df4f9b17ad2b417be66c3710"
    ciphertext = b"c04b05357c5d1c0eeac4c66f9ff7f2e6"


class Test_AES_CFB_192_v1(CipherTests, unittest.TestCase):

    algorithm = b"AES-192-CFB"
    key = b"8e73b0f7da0e6452c810f32b809079e562f8ead2522c6b7b"
    iv = b"000102030405060708090A0B0C0D0E0F"
    plaintext = b"6bc1bee22e409f96e93d7e117393172a"
    ciphertext = b"cdc80d6fddf18cab34c25909c99a4174"


class Test_AES_CFB_192_v2(CipherTests, unittest.TestCase):

    algorithm = b"AES-192-CFB"
    key = b"8e73b0f7da0e6452c810f32b809079e562f8ead2522c6b7b"
    iv = b"CDC80D6FDDF18CAB34C25909C99A4174"
    plaintext = b"ae2d8a571e03ac9c9eb76fac45af8e51"
    ciphertext = b"67ce7f7f81173621961a2b70171d3d7a"


class Test_AES_CFB_192_v3(CipherTests, unittest.TestCase):

    algorithm = b"AES-192-CFB"
    key = b"8e73b0f7da0e6452c810f32b809079e562f8ead2522c6b7b"
    iv = b"67CE7F7F81173621961A2B70171D3D7A"
    plaintext = b"30c81c46a35ce411e5fbc1191a0a52ef"
    ciphertext = b"2e1e8a1dd59b88b1c8e60fed1efac4c9"


class Test_AES_CFB_192_v4(CipherTests, unittest.TestCase):

    algorithm = b"AES-192-CFB"
    key = b"8e73b0f7da0e6452c810f32b809079e562f8ead2522c6b7b"
    iv = b"2E1E8A1DD59B88B1C8E60FED1EFAC4C9"
    plaintext = b"f69f2445df4f9b17ad2b417be66c3710"
    ciphertext = b"c05f9f9ca9834fa042ae8fba584b09ff"


class Test_AES_CFB_256_v1(CipherTests, unittest.TestCase):

    algorithm = b"AES-256-CFB"
    key = b"603deb1015ca71be2b73aef0857d77811f352c073b6108d72d9810a30914dff4"
    iv = b"000102030405060708090A0B0C0D0E0F"
    plaintext = b"6bc1bee22e409f96e93d7e117393172a"
    ciphertext = b"DC7E84BFDA79164B7ECD8486985D3860"


class Test_AES_CFB_256_v2(CipherTests, unittest.TestCase):

    algorithm = b"AES-256-CFB"
    key = b"603deb1015ca71be2b73aef0857d77811f352c073b6108d72d9810a30914dff4"
    iv = b"DC7E84BFDA79164B7ECD8486985D3860"
    plaintext = b"ae2d8a571e03ac9c9eb76fac45af8e51"
    ciphertext = b"39ffed143b28b1c832113c6331e5407b"


class Test_AES_CFB_256_v3(CipherTests, unittest.TestCase):

    algorithm = b"AES-256-CFB"
    key = b"603deb1015ca71be2b73aef0857d77811f352c073b6108d72d9810a30914dff4"
    iv = b"39FFED143B28B1C832113C6331E5407B"
    plaintext = b"30c81c46a35ce411e5fbc1191a0a52ef"
    ciphertext = b"df10132415e54b92a13ed0a8267ae2f9"


class Test_AES_CFB_256_v4(CipherTests, unittest.TestCase):

    algorithm = b"AES-256-CFB"
    key = b"603deb1015ca71be2b73aef0857d77811f352c073b6108d72d9810a30914dff4"
    iv = b"DF10132415E54B92A13ED0A8267AE2F9"
    plaintext = b"f69f2445df4f9b17ad2b417be66c3710"
    ciphertext = b"75a385741ab9cef82031623d55b1e471"


class Test_AES_OFB_128_v1(CipherTests, unittest.TestCase):

    algorithm = b"AES-128-OFB"
    key = b"2b7e151628aed2a6abf7158809cf4f3c"
    iv = b"000102030405060708090A0B0C0D0E0F"
    plaintext = b"6bc1bee22e409f96e93d7e117393172a"
    ciphertext = b"3b3fd92eb72dad20333449f8e83cfb4a"


class Test_AES_OFB_128_v2(CipherTests, unittest.TestCase):

    algorithm = b"AES-128-OFB"
    key = b"2b7e151628aed2a6abf7158809cf4f3c"
    iv = b"50FE67CC996D32B6DA0937E99BAFEC60"
    plaintext = b"ae2d8a571e03ac9c9eb76fac45af8e51"
    ciphertext = b"7789508d16918f03f53c52dac54ed825"


class Test_AES_OFB_128_v3(CipherTests, unittest.TestCase):

    algorithm = b"AES-128-OFB"
    key = b"2b7e151628aed2a6abf7158809cf4f3c"
    iv = b"D9A4DADA0892239F6B8B3D7680E15674"
    plaintext = b"30c81c46a35ce411e5fbc1191a0a52ef"
    ciphertext = b"9740051e9c5fecf64344f7a82260edcc"


class Test_AES_OFB_128_v4(CipherTests, unittest.TestCase):

    algorithm = b"AES-128-OFB"
    key = b"2b7e151628aed2a6abf7158809cf4f3c"
    iv = b"A78819583F0308E7A6BF36B1386ABF23"
    plaintext = b"f69f2445df4f9b17ad2b417be66c3710"
    ciphertext = b"304c6528f659c77866a510d9c1d6ae5e"


class Test_AES_OFB_192_v1(CipherTests, unittest.TestCase):

    algorithm = b"AES-192-OFB"
    key = b"8e73b0f7da0e6452c810f32b809079e562f8ead2522c6b7b"
    iv = b"000102030405060708090A0B0C0D0E0F"
    plaintext = b"6bc1bee22e409f96e93d7e117393172a"
    ciphertext = b"cdc80d6fddf18cab34c25909c99a4174"


class Test_AES_OFB_192_v2(CipherTests, unittest.TestCase):

    algorithm = b"AES-192-OFB"
    key = b"8e73b0f7da0e6452c810f32b809079e562f8ead2522c6b7b"
    iv = b"A609B38DF3B1133DDDFF2718BA09565E"
    plaintext = b"ae2d8a571e03ac9c9eb76fac45af8e51"
    ciphertext = b"fcc28b8d4c63837c09e81700c1100401"


class Test_AES_OFB_192_v3(CipherTests, unittest.TestCase):

    algorithm = b"AES-192-OFB"
    key = b"8e73b0f7da0e6452c810f32b809079e562f8ead2522c6b7b"
    iv = b"52EF01DA52602FE0975F78AC84BF8A50"
    plaintext = b"30c81c46a35ce411e5fbc1191a0a52ef"
    ciphertext = b"8d9a9aeac0f6596f559c6d4daf59a5f2"


class Test_AES_OFB_192_v4(CipherTests, unittest.TestCase):

    algorithm = b"AES-192-OFB"
    key = b"8e73b0f7da0e6452c810f32b809079e562f8ead2522c6b7b"
    iv = b"BD5286AC63AABD7EB067AC54B553F71D"
    plaintext = b"f69f2445df4f9b17ad2b417be66c3710"
    ciphertext = b"6d9f200857ca6c3e9cac524bd9acc92a"


class Test_AES_OFB_256_v1(CipherTests, unittest.TestCase):

    algorithm = b"AES-256-OFB"
    key = b"603deb1015ca71be2b73aef0857d77811f352c073b6108d72d9810a30914dff4"
    iv = b"000102030405060708090A0B0C0D0E0F"
    plaintext = b"6bc1bee22e409f96e93d7e117393172a"
    ciphertext = b"dc7e84bfda79164b7ecd8486985d3860"


class Test_AES_OFB_256_v2(CipherTests, unittest.TestCase):

    algorithm = b"AES-256-OFB"
    key = b"603deb1015ca71be2b73aef0857d77811f352c073b6108d72d9810a30914dff4"
    iv = b"B7BF3A5DF43989DD97F0FA97EBCE2F4A"
    plaintext = b"ae2d8a571e03ac9c9eb76fac45af8e51"
    ciphertext = b"4febdc6740d20b3ac88f6ad82a4fb08d"


class Test_AES_OFB_256_v3(CipherTests, unittest.TestCase):

    algorithm = b"AES-256-OFB"
    key = b"603deb1015ca71be2b73aef0857d77811f352c073b6108d72d9810a30914dff4"
    iv = b"E1C656305ED1A7A6563805746FE03EDC"
    plaintext = b"30c81c46a35ce411e5fbc1191a0a52ef"
    ciphertext = b"71ab47a086e86eedf39d1c5bba97c408"


class Test_AES_OFB_256_v4(CipherTests, unittest.TestCase):

    algorithm = b"AES-256-OFB"
    key = b"603deb1015ca71be2b73aef0857d77811f352c073b6108d72d9810a30914dff4"
    iv = b"41635BE625B48AFC1666DD42A09D96E7"
    plaintext = b"f69f2445df4f9b17ad2b417be66c3710"
    ciphertext = b"0126141d67f37be8538f5a8be740e484"
