# Copyright (c) 2014 apporc
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import logging
from twisted.python import log
import json

CONFIG_PATH = os.environ['HOME'] + '/.config/' + 'shadowsocks-gtk/'
CONFIG_FILE = 'config.json'


def get_config():
    path = CONFIG_PATH + CONFIG_FILE
    if os.path.exists(path):
        with open(path, 'rb') as f:
            options = json.load(f)
        return options
    else:
        return {}


def save_config(config):
    if not os.path.exists(CONFIG_PATH):
        os.makedirs(CONFIG_PATH)
    path = CONFIG_PATH + CONFIG_FILE
    with open(path, 'wb') as f:
        json.dump(config, f)


def start_log(level=logging.INFO):
    observer = logger(level)
    log.startLoggingWithObserver(observer)


def logger(loglevel):
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    logging.basicConfig(
        format='%(asctime)s-[%(levelname)s]-%(name)s :  %(message)s',
        level=numeric_level)
    observer = log.PythonLoggingObserver()
    return observer.emit
