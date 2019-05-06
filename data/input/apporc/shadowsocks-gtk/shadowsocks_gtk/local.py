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

from twisted.internet import protocol, reactor
from twisted.protocols.policies import TimeoutMixin
import struct
from utils import get_config, start_log
import logging
logger = logging.getLogger()

import encrypt
config = get_config()


STATE_INITIAL = 0
STATE_AUTH = 1
STATE_REQUEST = 2
STATE_READY = 3
STATE_AUTH_USERPASS = 4
STATE_LAST = 5

STATE_CONNECT_PENDING = STATE_LAST + 1

SOCKS5_VER = 0x05

ADDR_IPV4 = 0x01
ADDR_DOMAINNAME = 0x03
ADDR_IPV6 = 0x04

CMD_CONNECT = 0x01
CMD_BIND = 0x02
CMD_UDPASSOC = 0x03

AUTHMECH_ANON = 0x00
AUTHMECH_USERPASS = 0x02
AUTHMECH_INVALID = 0xFF

REPLY_SUCCESS = 0x00
REPLY_GENERAL_FAILUR = 0x01
REPLY_CONN_NOT_ALLOWED = 0x02
REPLY_NETWORK_UNREACHABLE = 0x03
REPLY_HOST_UNREACHABLE = 0x04
REPLY_CONN_REFUSED = 0x05
REPLY_TTL_EXPIRED = 0x06
REPLY_CMD_NOT_SUPPORTED = 0x07
REPLY_ADDR_NOT_SUPPORTED = 0x08


class SOCKSv5Outgoing(protocol.Protocol):
    def __init__(self, peersock):
        self.peersock = peersock
        self.peersock.peersock = self

    def connectionMade(self):
        logger.info('Connected to %s' % self.peersock.server)
        self.peersock.connectCompleted()

    def connectionLost(self, reason):
        logger.info('Lost connection to %s' % self.peersock.server)
        self.peersock.transport.loseConnection()
        self.peersock.peersock = None
        self.peersock = None

    def dataReceived(self, buf):
        buf = self.peersock.encryptor.decrypt(buf)
        self.peersock.transport.write(buf)


class SOCKSv5(protocol.Protocol, TimeoutMixin):

    def __init__(self):
        self.server = config['server']
        self.server_port = config['server_port']
        self.timeout = config['timeout']
        self.data_to_send = []
        self.state = STATE_INITIAL
        self.buf = ""
        self.supportedAuthMechs = [AUTHMECH_ANON, AUTHMECH_USERPASS]
        self.supportedAddrs = [ADDR_IPV4, ADDR_DOMAINNAME]
        self.enabledCommands = [CMD_CONNECT, CMD_UDPASSOC]
        self.peersock = None
        self.addressType = 0
        self.requestType = 0
        self.encryptor = encrypt.Encryptor(config['password'],
                                           config['method'])

    def _parseNegotiation(self):
        try:
            # Parse out data
            ver, nmethod = struct.unpack('!BB', self.buf[:2])
            methods = struct.unpack('%dB' % nmethod, self.buf[2:nmethod+2])

            # Ensure version is correct
            if ver != 5:
                self.transport.write(struct.pack('!BB', SOCKS5_VER, AUTHMECH_INVALID))
                self.transport.loseConnection()
                return

            # Trim off front of the buffer
            self.buf = self.buf[nmethod+2:]

            # Check for supported auth mechs
            for m in self.supportedAuthMechs:
                if m in methods:
                    # Update internal state, according to selected method
                    if m == AUTHMECH_ANON:
                        self.state = STATE_REQUEST
                    elif m == AUTHMECH_USERPASS:
                        self.state = STATE_AUTH_USERPASS
                    # Complete negotiation w/ this method
                    self.transport.write(struct.pack('!BB', SOCKS5_VER, m))
                    return

            # No supported mechs found, notify client and close the connection
            logger.error('Not supported mechs found')
            self.transport.write(struct.pack('!BB', SOCKS5_VER, AUTHMECH_INVALID))
            self.transport.loseConnection()
        except struct.error:
            pass

    def _parseUserPass(self):
        try:
            # Parse out data
            ver, ulen = struct.unpack('BB', self.buf[:2])
            uname, = struct.unpack('%ds' % ulen, self.buf[2:ulen + 2])
            plen, = struct.unpack('B', self.buf[ulen + 2])
            password, = struct.unpack('%ds' % plen, self.buf[ulen + 3:ulen + 3 + plen])
            # Trim off fron of the buffer
            self.buf = self.buf[3 + ulen + plen:]
            # Fire event to authenticate user
            if self.authenticateUserPass(uname, password):
                # Signal success
                self.state = STATE_REQUEST
                self.transport.write(struct.pack('!BB', SOCKS5_VER, 0x00))
            else:
                # Signal failure
                self.transport.write(struct.pack('!BB', SOCKS5_VER, 0x01))
                self.transport.loseConnection()
        except struct.error:
            pass

    def sendErrorReply(self, errorcode):
        # Any other address types are not supported
        result = struct.pack('!BBBBIH', SOCKS5_VER, errorcode, 0, 1, 0, 0)
        self.transport.write(result)
        self.transport.loseConnection()

    def _parseRequest(self):
        try:
            # Parse out data and trim buffer accordingly
            ver, cmd, rsvd, self.addressType = struct.unpack('!BBBB', self.buf[:4])

            # Ensure command is supported
            if cmd not in self.enabledCommands:
                # Send a not supported error
                self.sendErrorReply(REPLY_CMD_NOT_SUPPORTED)
                return

            # Process the command
            if cmd == CMD_CONNECT:
                result = '\x05\x00\x00\x01\x00\x00\x00\x00\x10\x10'
                self.transport.write(result)
                self.data_to_send.append(self.encryptor.encrypt(self.buf[3:]))
                self.connectServer(self.server, self.server_port)
            elif cmd == CMD_UDPASSOC:
                logger .warn('Got UDP ASSOC request!!')
            else:
                # Any other command is not supported
                self.sendErrorReply(REPLY_CMD_NOT_SUPPORTED)

        except struct.error:
            return None

    def connectServer(self, addr, port):
        self.transport.stopReading()
        self.state = STATE_CONNECT_PENDING
        protocol.ClientCreator(reactor, SOCKSv5Outgoing, self).connectTCP(addr, port)

    def connectCompleted(self):
        self.state = STATE_READY
        self.transport.startReading()

    def authenticateUserPass(self, user, passwd):
        logger.info("User/pass: %s/%s" % (user, passwd))
        return True

    def connectionMade(self):
        self.setTimeout(self.timeout)

    def dataReceived(self, buf):
        self.resetTimeout()

        if self.state == STATE_READY:
            self.data_to_send.append(self.encryptor.encrypt(buf))
            data = ''.join(self.data_to_send)
            self.data_to_send = []
            self.peersock.transport.write(data)
            return

        self.buf = self.buf + buf
        if self.state == STATE_INITIAL:
            self._parseNegotiation()
        if self.state == STATE_AUTH_USERPASS:
            self._parseUserPass()
        if self.state == STATE_REQUEST:
            self._parseRequest()

    def timeoutConnection(self):
        logger.warn('Connection timedout!')
        self.transport.unregisterProducer()
        self.transport.loseConnection()


def main():
    factory = protocol.Factory()
    factory.protocol = SOCKSv5
    start_log(config['level'])
    encrypt.init_table(config['password'], config['method'])
    reactor.listenTCP(config['local_port'], factory)
    reactor.run()

if __name__ == "__main__":
    main()
