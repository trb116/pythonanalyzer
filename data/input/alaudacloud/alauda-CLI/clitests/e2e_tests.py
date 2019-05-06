import unittest
import uuid
import shutil
import time
import os
from alaudacli import cmd_parser, cmd_processor, service, auth
from alaudacli.service import Service


class ServiceTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        try:
            service.Service.remove('test-hello')
        except:
            pass
        try:
            service.Service.remove('test-mysql')
        except:
            pass
        api_endpoint, token, username = auth.load_token()
        if '.io' in api_endpoint:
            cls.registry = 'index.alauda.io'
        else:
            cls.registry = 'index.alauda.cn'

    def _create_service(self, name, image, port, start=False, volume='', envvar='', link=''):
        cmd = 'create'
        if start:
            cmd = 'run'

        argv = ['service', cmd, name, image, '-p', str(port)]
        if volume:
            argv += ['-v', volume]
        if envvar:
            argv += ['-e', envvar]

        args = cmd_parser.parse_cmds(argv)
        cmd_processor.process_cmds(args)

    def _wait_for_service(self, name, timeout_in_seconds=60):
        for i in range(0, timeout_in_seconds):
            service = Service.fetch(name)
            if service.get_state() == 'Deploying':
                time.sleep(1)
                continue
            elif service.get_state() == 'Running':
                print 'Service {0} is running'.format(name)
                return
            elif service.get_state() == 'Stopped':
                print 'Service {0} is not running'.format(name)
                return
            else:
                raise Exception('Service {0} failed to deploy'.format(name))
        raise Exception('Timed out waiting for service {0}'.format(name))

    def _start_service(self, name):
        argv = ['service', 'start', name]
        args = cmd_parser.parse_cmds(argv)
        cmd_processor.process_cmds(args)
        self._wait_for_service('test-hello')

    def _list_services(self):
        argv = ['service', 'ps']
        args = cmd_parser.parse_cmds(argv)
        cmd_processor.process_cmds(args)

    def _inspect_service(self, name):
        argv = ['service', 'inspect', name]
        args = cmd_parser.parse_cmds(argv)
        cmd_processor.process_cmds(args)

    def _get_service_logs(self, name):
        argv = ['service', 'logs', name]
        args = cmd_parser.parse_cmds(argv)
        cmd_processor.process_cmds(args)

    def _scale_service(self, name, target_num_instances):
        argv = ['service', 'scale', '{0}={1}'.format(name, target_num_instances)]
        args = cmd_parser.parse_cmds(argv)
        cmd_processor.process_cmds(args)

    def _stop_service(self, name):
        argv = ['service', 'stop', name]
        args = cmd_parser.parse_cmds(argv)
        cmd_processor.process_cmds(args)

    def _remove_service(self, name):
        argv = ['service', 'rm', name]
        args = cmd_parser.parse_cmds(argv)
        cmd_processor.process_cmds(args)

    def _enable_autoscaling(self, name, config):
        argv = ['service', 'enable-autoscaling', name, '-f', config]
        args = cmd_parser.parse_cmds(argv)
        cmd_processor.process_cmds(args)

    def _disable_autoscaling(self, name):
        argv = ['service', 'disable-autoscaling', name]
        args = cmd_parser.parse_cmds(argv)
        cmd_processor.process_cmds(args)

    def test_stateless_service(self):
        name = 'test-hello'
        image = self.registry + '/alauda/hello-world'

        # create service
        self._create_service(name, image, 80)
        self._wait_for_service(name)

        # start
        self._start_service(name)

        # ps
        self._list_services()

        # inspect
        self._inspect_service(name)

        # logs
        self._get_service_logs(name)

        # scale
        self._scale_service(name, 2)
        self._wait_for_service(name)

        # enable auto-scaling
        self._enable_autoscaling(name, 'clitests/auto-scaling.cfg')
        self._wait_for_service(name)

        # disable auto-scaling
        self._disable_autoscaling(name)
        self._wait_for_service(name)

        # stop
        self._stop_service(name)
        self._wait_for_service(name)

        # remove
        self._remove_service(name)

    def test_stateful_service(self):
        name = 'test-mysql'
        image = self.registry + '/alauda/mysql'

        # create service
        self._create_service(name, image, 3306, True,
                             volume='/var/lib/mysql:10',
                             envvar='MYSQL_ROOT_PASSWORD=root')
        self._wait_for_service(name)

        # inspect
        self._inspect_service(name)

        # stop
        self._stop_service(name)
        self._wait_for_service(name)

        # remove
        self._remove_service(name)

    def test_service_linking(self):
        db = 'test-mysql'
        db_image = self.registry + '/alauda/mysql'
        web = 'test-hello'
        web_image = self.registry + '/alauda/hello-world'

        # create db
        self._create_service(db, db_image, 3306, True,
                             volume='/var/lib/mysql:10',
                             envvar='MYSQL_ROOT_PASSWORD=root')
        self._wait_for_service(db)

        # create web
        self._create_service(web, web_image, 80,
                             link='test-mysql:db')
        self._wait_for_service(web)

        # remove
        self._remove_service(web)
        self._remove_service(db)


class BuildTest(unittest.TestCase):

    def setUp(self):
        self.repo_name = 'fileupload-test'
        self.namespace = 'mathildedev'

        self.source_path = '/tmp/alaudacli/{}'.format(uuid.uuid4())
        os.makedirs(self.source_path)
        with open(os.path.join(self.source_path, 'Dockerfile'), 'w') as f:
            f.writelines([
                'FROM ubuntu:14.04\n', 'CMD ["echo hello"]\n'
            ])

    def tearDown(self):
        shutil.rmtree(self.source_path)

    def test_create_build(self):
        argv = [
            'build', 'create', '-p', self.source_path, '-rn', self.repo_name,
            '-n', self.namespace, '-t', 'latest'
        ]
        args = cmd_parser.parse_cmds(argv)
        cmd_processor.process_cmds(args)
