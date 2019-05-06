#-*- coding: utf-8 -*-
"""
:Author:    Arne Simon [arne.simon@slice-dice.de]
"""
import json
import os
import pytest

from aboutyou.api import Api
from aboutyou.auth import Auth
from aboutyou.config import YAMLConfig, YAMLCredentials
from aboutyou.shop import ShopApi


config = YAMLConfig('examples/config.yaml')
credentials = YAMLCredentials('test/data/credentials.yml')


def read(filename):
    with open(os.path.join('test', 'data', filename)) as src:
        return src.read()


@pytest.fixture
def mock(monkeypatch):
    def wrapper(filename):
        def request(self, params):
            return read(filename)

        monkeypatch.setattr("aboutyou.api.Api.request", request)

        with open(os.path.join('test', 'data', filename)) as src:
            return json.load(src)

    return wrapper


@pytest.fixture
def auth():
    return Auth(credentials, config)


@pytest.fixture
def aboutyou():
    return Api(credentials, config)


@pytest.fixture
def shop(monkeypatch):
    client = ShopApi(credentials, config)

    monkeypatch.setattr("aboutyou.api.Api.request", lambda self, params: read('category-tree.json'))

    client.categories()

    monkeypatch.setattr("aboutyou.api.Api.request", lambda self, params: read('facets-all.json'))

    client.facet_groups()

    return client


@pytest.fixture
def session():
    return 's3ss10n'


@pytest.fixture
def log(request, aboutyou):
    return aboutyou.log.getChild(request.function.__name__)
