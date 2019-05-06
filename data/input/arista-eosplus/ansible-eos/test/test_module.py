import os
import subprocess
import json
import shlex

from string import Template
from ConfigParser import SafeConfigParser

import yaml

import pyeapi

nodes = dict()
testcases = list()
config = SafeConfigParser()

here = os.path.abspath(os.path.dirname(__file__))

class TestCase(object):

    def __init__(self, **kwargs):
        self.name = kwargs['name']
        self.module = kwargs['module']
        self.module_path = kwargs['module_path']

        self.host = None

        self.inventory = kwargs.get('inventory')
        self.exitcode = kwargs.get('exitcode', 0)
        self.idempotent = kwargs.get('idempotent', True)
        self.changed = kwargs.get('changed', True)

        self.arguments = kwargs.get('arguments', list())
        self.variables = dict()

        # optional properties
        self.setup = kwargs.get('setup', list())
        self.teardown = kwargs.get('teardown', list())

        # runtime properties
        self._command = None

    def __str__(self):
        return self.name

    @property
    def command(self):
        if self._command:
            return self._command
        self._command = self._build_command()
        return self._command

    def set_host(self, value):
        self.host = value

    def add_variable(self, name, value):
        self.variables[name] = value

    def _build_command(self):
        command = ['ansible']

        if self.inventory:
            command.extend(['-i', self.inventory])

        modpath = '{}'.format(self.module_path)
        command.extend(['-M', modpath])
        command.extend(['-m', self.module])
        command.extend(['-e', 'ansible_python_interpreter=python'])
        command.extend(['--connection', 'local'])

        arguments = ''
        for arg in self.arguments:
            arguments += '%s=\'%s\' ' % (arg['name'], arg['value'])
        command.extend(['-a', '"%s"' % arguments.strip()])

        command.append(self.host)

        return command


class TestModule(object):

    def __init__(self, testcase, node):
        self.testcase = testcase
        self.node = node
        self.description = 'Test[%s]: %s' % (testcase.module, testcase.name)

    def __call__(self):
        self.output('Run first pass')
        response = self.run_module()
        assert response['changed'] == self.testcase.changed

        if self.testcase.idempotent:
            self.output('Run second pass')
            response = self.run_module()
            assert not response['changed']

    def setUp(self):
        if self.testcase.setup:
            try:
                self.output('Running setup commands')
                self.output(self.testcase.setup)
                self.node.config(self.testcase.setup)
            except pyeapi.eapilib.CommandError as exc:
                print exc
                print self.testcase.setup
                raise

    def tearDown(self):
        if self.testcase.teardown:
            self.output('Running teardown commands')
            self.output(self.testcase.teardown)
            self.node.config(self.testcase.teardown)

    def output(self, text):
        print '>>', str(text)

    def run_module(self):
        (retcode, out, err) = self.execute_module()
        assert(retcode == self.testcase.exitcode)
        return self.parse_response(out)

    def parse_response(self, output):
        try:
            resp = json.loads(str(output).split(' >> ')[1])
        except:
            resp = json.loads(str(output).split(' => ')[1])

        return resp

    def compile_command(self):
        command = ' '.join(self.testcase.command)
        command = Template(command).safe_substitute(self.testcase.variables)
        return shlex.split(command)

    def execute_module(self):
        command = self.compile_command()
        self.output('command: %s' % ' '.join(command))

        stdout = subprocess.PIPE
        stderr = subprocess.PIPE

        proc = subprocess.Popen(command, stdout=stdout, stderr=stderr)
        out, err = proc.communicate()

        self.output(out)
        self.output(err)
        return (proc.returncode, out, err)

def filter_modules(modules, filenames):
    if modules:
        modules = ['{0}.yaml'.format(s) for s in modules.split(',')]
        return list(set(modules).intersection(filenames))
    return filenames

def setup():
    pyeapi.load_config(os.path.join(here, 'fixtures/eapi.conf'))
    for name in pyeapi.client.config.connections:
        if name != 'localhost':
            nodes[name] = pyeapi.connect_to(name)

    assert len(nodes) > 0, 'no test nodes loaded, does eapi.conf exist?'

    modules = os.environ.get('ANSIBLE_TEST_CASES')

    testcases_home = os.path.join(here, 'testcases')
    filenames = os.listdir(testcases_home)

    for module in filter_modules(modules, filenames):
        path = os.path.join(testcases_home, module)
        definition = yaml.load(open(path))

        defaults = definition.get('defaults', {})
        for testcase in definition['testcases']:
            kwargs = defaults.copy()
            kwargs.update(testcase)
            testcases.append(TestCase(**kwargs))


def test_module():
    for name, node in nodes.items():
        for testcase in testcases:
            testcase.set_host(name)
            testcase.add_variable('host', name)
            yield TestModule(testcase, node)
