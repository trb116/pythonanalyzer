import util
import auth
import requests


class Instance(object):

    def __init__(self, service=None, uuid='', details=None):
        self.service = service
        self.uuid = uuid
        self.details = details

    def inspect(self):
        return self.details

    def logs(self, start_time, end_time):
        start, end = util.parse_time(start_time, end_time)
        api_endpoint, token, _ = auth.load_token()
        url = api_endpoint + 'services/{0}/{1}/instances/{2}/logs?start_time={3}&end_time={4}'.format(self.service.namespace,
                                                                                                      self.service.name,
                                                                                                      self.uuid, start, end)
        headers = auth.build_headers(token)
        r = requests.get(url, headers=headers)
        util.check_response(r)
        return r.text
