#-*- coding: utf-8 -*-
"""
:Author: Arne Simon [arne.simon@slice-dice.de]
"""
from aboutyou.config import *


def test_credentials():
    cred = Credentials(200, "1234", "5678")

    assert cred.authorization == 'Basic MjAwOjU2Nzg='


def test_yaml_credentials():
    cred = YAMLCredentials('test/data/credentials.yml')

    assert cred.authorization == 'Basic MjAwOjU2Nzg='
    assert cred.endpoint == 'live'


def test_json_credentials():
    cred = JSONCredentials('test/data/credentials.json')

    assert cred.authorization == 'Basic MjAwOjU2Nzg='
    assert cred.endpoint == 'live'


def test_config():
    conf = Config()


def simelarity(conf):
    con = Config()

    for key in ["live_url", "stage_url", "image_url", "product_url", "shop_url", "javascript_url"]:
        assert getattr(con, key) == getattr(conf, key)


def test_yaml_config():
    conf = YAMLConfig('examples/config.yaml')

    simelarity(conf)


def test_json_config():
    conf = JSONConfig('examples/config.json')

    simelarity(conf)


def test_json_env_config():
    conf = JSONEnvironmentFallbackConfig('examples/config.json')

    simelarity(conf)
