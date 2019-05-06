import util
import auth
import json
import requests


class Organization(object):

    def __init__(self, name, company, details=''):
        self.name = name
        self.company = company
        self.details = details

    def create(self):
        api_endpoint, token, _ = auth.load_token()
        headers = auth.build_headers(token)
        url = api_endpoint + 'orgs/'
        payload = {
            'name': self.name,
            'company': self.company
        }
        r = requests.post(url, headers=headers, data=json.dumps(payload))
        util.check_response(r)

    @classmethod
    def fetch(cls, name):
        api_endpoint, token, _ = auth.load_token()
        headers = auth.build_headers(token)
        url = api_endpoint + 'orgs/{}/'.format(name)
        r = requests.get(url, headers=headers)
        util.check_response(r)
        result = json.loads(r.text)
        organization = cls(result['name'], result['company'], r.text)
        return organization

    @classmethod
    def list(cls):
        api_endpoint, token, _ = auth.load_token()
        headers = auth.build_headers(token)
        url = api_endpoint + 'orgs/'
        r = requests.get(url, headers=headers)
        util.check_response(r)
        organization_list = []
        if r.text:
            organizations = json.loads(r.text)
            for data in organizations:
                organization = Organization.fetch(data['name'])
                organization_list.append(organization)
        return organization_list

    def update(self, company):
        api_endpoint, token, _ = auth.load_token()
        headers = auth.build_headers(token)
        url = api_endpoint + 'orgs/{}/'.format(self.name)
        payload = {
            'company': company
        }
        r = requests.put(url, headers=headers, data=json.dumps(payload))
        util.check_response(r)

    def inspect(self):
        return self.details
