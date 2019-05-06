import json
import os

import settings
from exceptions import AlaudaInputError


def get_api_endpoint(cloud):
    return settings.API_ENDPOINTS[cloud]


def save_token(api_endpoint, token, username):
    auth = {
        'endpoint': api_endpoint,
        "token": token
    }
    config = {
        'auth': auth,
        'username': username
    }
    with open(settings.ALAUDACFG, 'w') as f:
        json.dump(config, f, indent=2)


def load_token():
    try:
        with open(settings.ALAUDACFG, 'r') as f:
            config = json.load(f)
            api_endpoint = config['auth']['endpoint']
            token = config['auth']['token']
            username = config['username']
            return api_endpoint, token, username
    except:
        raise AlaudaInputError('Please login first')


def delete_token():
    try:
        os.remove(settings.ALAUDACFG)
    except:
        print '[alauda] Already logged out'


def build_headers(token):
    headers = {
        'Authorization': 'Token ' + token,
        'Content-type': 'application/json'
    }
    return headers
