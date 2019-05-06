import util
import auth
import json
import requests
from exceptions import AlaudaServerError


class Backup(object):

    def __init__(self, service=None, name='', mounted_dir='', details=''):
        self.service = service
        self.name = name
        self.mounted_dir = mounted_dir
        self.details = details

    def create(self):
        print '[alauda] Creating backup "{}"'.format(self.name)
        url = self.service.api_endpoint + 'backups/{}/'.format(self.service.namespace)
        data = json.loads(self.service.details)
        payload = {
            'app_id': data['unique_name'],
            'name': self.name,
            'app_volume_dir': self.mounted_dir
        }
        r = requests.post(url, headers=self.service.headers, data=json.dumps(payload))
        util.check_response(r)

    @classmethod
    def fetch(cls, id, namespace=None):
        api_endpoint, token, username = auth.load_token()
        url = api_endpoint + 'backups/{0}/{1}/'.format(namespace or username, id)
        headers = auth.build_headers(token)
        r = requests.get(url, headers=headers)
        util.check_response(r)
        data = json.loads(r.text)
        backup = cls(name=data['name'], details=r.text)
        return backup

    @classmethod
    def list(cls, namespace=None):
        api_endpoint, token, username = auth.load_token()
        url = api_endpoint + 'backups/{}/'.format(namespace or username)
        headers = auth.build_headers(token)
        r = requests.get(url, headers=headers)
        util.check_response(r)
        backups = json.loads(r.text)
        backup_list = []
        for data in backups:
            backup = Backup.fetch(data['backup_id'], namespace)
            backup_list.append(backup)
        return backup_list

    def inspect(self):
        return self.details

    @classmethod
    def remove(cls, id, namespace=None):
        api_endpoint, token, username = auth.load_token()
        url = api_endpoint + 'backups/{0}/{1}/'.format(namespace or username, id)
        headers = auth.build_headers(token)
        r = requests.delete(url, headers=headers)
        try:
            util.check_response(r)
        except AlaudaServerError as ex:
            if ex.status_code == 400:
                print '[alauda] backup "{}" does not exist'.format(id)
            else:
                raise ex
