import getpass
import paramiko
import json
import requests

import interactive
import auth
import util
from exceptions import AlaudaExecError


class Executer(object):

    def __init__(self, name, username, namespace, exec_endpoint='exec.alauda.cn', verbose=False):
        self.name = name if username == namespace else '{}/{}'.format(namespace, name)
        self.namespace = namespace
        self.username = username
        self.exec_endpoint = exec_endpoint
        self.port = 4022
        self.client = None
        self.chan = None
        self.verbose = verbose

    def connect(self):
        if self.verbose:
            print('*** Connecting...')

        # connect to the exec_endpoint
        self.client = paramiko.SSHClient()
        self.client.load_system_host_keys()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        password = getpass.getpass('Password for %s@%s: ' % (self.username, self.exec_endpoint))
        self.client.connect(self.exec_endpoint,
                            self.port,
                            username=self.username,
                            password=password,
                            allow_agent=False,
                            look_for_keys=False)

        if self.verbose:
            print(repr(self.client.get_transport()))

    def execute(self, command, *args):
        try:
            self.connect()
            transport = self.client.get_transport()
            self.chan = transport.open_session()
            self.chan.get_pty()
            self.chan.exec_command('{} {} {}'.format(self.name, command, ' '.join(args)))
            interactive.interactive_shell(self.chan)
            self.close()
        except Exception as e:
            try:
                self.close()
            except:
                pass
            raise AlaudaExecError('Executing \'{}\' failed with \'{}\''.format(command, e))

    def close(self):
        if self.chan:
            self.chan.close()
        self.client.close()

    @classmethod
    def fetch(cls, name, namespace=None):
        service_name = name.split(".")[0]

        api_endpoint, token, username = auth.load_token()
        url = api_endpoint + 'services/{}/'.format(namespace or username) + service_name
        headers = auth.build_headers(token)
        r = requests.get(url, headers=headers)
        util.check_response(r)
        data = json.loads(r.text)
        executer = cls(name=name,
                       username=username,
                       exec_endpoint=data['exec_endpoint'],
                       namespace=data['namespace'])
        return executer
