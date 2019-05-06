#!/usr/bin/env python

from setuptools import setup
import re
import sys

import tls.c


def load_version(filename='tls/version.py'):
    "Parse a __version__ number from a source file"
    with open(filename) as source:
        text = source.read()
        match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", text)
        if not match:
            msg = "Unable to find version number in {}".format(filename)
            raise RuntimeError(msg)
        version = match.group(1)
        return version

PYTHON3K = sys.version_info[0] > 2

setup(
    name='opentls',
    version=load_version(),

    # Grab all of the Python packages we want to distribute or install,
    # top-level or otherwise.
    packages=['tls', 'tls.c', 'tls.io'],

    # Get cffi to define an extension module for the bindings, one that takes
    # advantage of cffi's caching and distribution features so we can build
    # binary packages that don't require the installer to have a compiler.
    ext_modules=[tls.c.api.ffi.verifier.get_extension()],

    # And put any cffi generated extension modules into the tls package instead
    # of leaving them lying around at the top-level as is the default (note
    # this value must agree with the value passed to the verify() call in the
    # implementation).
    ext_package="tls",

    # cffi-based packages are not zip-safe.
    zip_safe=False,

    author='Aaron Iles',
    author_email='aaron.iles@gmail.com',
    url='https://github.com/aliles/opentls',
    description='Cryptographic APIs for Python using OpenSSL',
    long_description=open('README.rst').read(),
    license='ASL',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Security :: Cryptography',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Networking'
    ],
    install_requires=['cffi==0.6'],
    tests_require=['mock'] + [] if PYTHON3K else ['unittest2'],
    test_suite="tests" if PYTHON3K else "unittest2.collector"
)
