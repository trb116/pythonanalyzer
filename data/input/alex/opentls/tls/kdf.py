"""Key Derivation Functions module.

 - pbkdf2(password, length, salt=None, iterations=1000):
    Uses PBKDF2 to generate a Secret object that includes the derived key. If
    salt is None a random salt of 8 bytes will be generated using the
    tls.random module.

Secret objects, which represented shared secrets, are named tuples with the
following properties.

 - key:        The derived key.
 - salt:       The salt used to seed the key derivation function.
 - iterations: The number of iterations used when deriving the key.
"""
from __future__ import absolute_import, division, print_function
from collections import namedtuple

from tls import random
from tls.c import api


__all__ = ['Secret', 'pbkdf2']


Secret = namedtuple('Secret', 'key salt iterations')


def pbkdf2(password, length, salt=None, iterations=1000):
    "Derive a shared secret including encryption key from password"
    if salt is None:
        salt = random.getrandbytes(8)
    c_password = api.new('char[]', password)
    c_salt = api.new('char[]', salt)
    c_key = api.new('unsigned char[]', length)
    api.PKCS5_PBKDF2_HMAC_SHA1(c_password, len(password),
        c_salt, len(salt), iterations, length, c_key)
    secret = Secret(api.buffer(c_key)[:], salt, iterations)
    return secret
