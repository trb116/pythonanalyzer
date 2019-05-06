#-*- coding: utf-8 -*-
"""
:Author:    Arne Simon [arne.simon@slice-dice.de]

.. autosummary::
    :nosignatures:

    Credentials
    YAMLCredentials
    JSONCredentials
    Config
    YAMLConfig
    JSONConfig
"""
import base64
import json
import logging.config
import os
import sys


class ConfigException(Exception):
    pass


class Credentials(object):
    """
    An interface for the app credentials.

    :param appid: The id for the application.
    :param app_token: The password aka token for the corresponding application id.
    :param appsecret: The corresponding secret for the application id.
    :param endpoint: Which API endpoint to use. ['live', 'stage']
    """
    def __init__(self, app_id, app_secret, app_token, endpoint='stage'):
        self.app_id = app_id
        self.app_secret = app_secret
        self.app_token = app_token
        self.endpoint = endpoint

    @property
    def authorization(self):
        """
        Content for the authorization header.
        """
        data = "{}:{}".format(self.app_id, self.app_token)

        if sys.version[0] == '2':
            encoded = base64.b64encode(data)
        else:
            encoded = base64.b64encode(bytes(data, "ascii"))

        return "Basic " + encoded.decode("ascii")


class JSONCredentials(Credentials):
        """
        Uses a JSON file to get the app credentials.

        :param filename: The path to the file.
        """
        def __init__(self, filename):
            with open(filename) as src:
                config = json.loads(src.read())

                super(JSONCredentials, self).__init__(config['app_id'], config['app_secret'], config['app_token'], config['endpoint'])


class Config(object):
    """
    The configuration of a Api api connection.

    A config class has to have the following readable attributes:

    :param entry_point_url: The url for Api.
    :param agent: The name of the browser agent to fake.
    :param image_url: A string as template for the image urls.
                        As example http://cdn.mary-paul.de/file/{}.
    :param product_url: The template for a product.
    :param shop_url: The url template for the shop.
    :param javascript_url: The URL to the Collins JavaScript file for helper functions
                             to add product variants into the basket of Mary & Paul or auto-resizing
                             the Iframe. This URL may be changed in future, so please use this method instead
                             of hardcoding the URL into your HTML template.
    :param auto_fetch: If set True, EasyApi fetches automaticly missing fields.
    :param cache: An dict {'hosts': ['server:11202'], 'timeout': 600}.
    :param dict logging: A dictonary for logging.config.dictConfig.
    """
    PARAMS = {"stage_url": "http://ant-core-staging-s-api1.wavecloud.de/api",
              "live_url": "https://shop-api.aboutyou.de/api",
              "agent": "Aboutyou-Shop-SDK-Python",
              "image_url": "http://cdn.mary-paul.de/file/{}",
              "product_url": "http://www.aboutyou.de/{}",
              "shop_url": "https://checkout.aboutyou.de/",
              "javascript_url":  "http://devcenter.dev/appjs/{}.js",
              "resource_url": "https://oauth.collins.kg/oauth",
              "auto_fetch": True,
              "cache": None,
              "logging": None}

    def __init__(self, **kwargs):
        for key, value in Config.PARAMS.items():
            setattr(self, key, value)

        for key, value in kwargs.items():
            if key in Config.PARAMS:
                setattr(self, key, value)
            else:
                raise ConfigException("unknown configuration key parameter")

        if "logging" in kwargs:
            logging.config.dictConfig(kwargs["logging"])


class JSONConfig(Config):
    """
    Uses a JSON file for configuration.

    :param jsonfile: The path to the json configuration file.

    .. literalinclude:: ../examples/config.json
        :language: json
    """
    def __init__(self, filename):
        with open(filename) as cfgfile:
            self.data = json.load(cfgfile)

        if "logging" in self.data and self.data["logging"] is not None:
            logging.config.dictConfig(self.data["logging"])

    def __getattr__(self, name):
        return self.data.get(name, None)


try:
    import yaml

    class YAMLConfig(Config):
        """
        Uses a YAML file for configuration.

        :param yamlfile: The path to the yaml configuration file.

        .. literalinclude:: ../examples/config.yaml
            :language: yaml
        """
        def __init__(self, filename):
            with open(filename) as cfgfile:
                self.data = yaml.load(cfgfile)

            if "logging" in self.data and self.data["logging"] is not None:
                logging.config.dictConfig(self.data["logging"])

        def __getattr__(self, name):
            return self.data.get(name, None)


    class YAMLCredentials(Credentials):
        """
        Uses a YAML file to get the app credentials.

        :param filename: The path to the file.

        .. literalinclude:: ../examples/credentials.yml
            :language: yaml

        """
        def __init__(self, filename):
            with open(filename) as src:
                config = yaml.load(src.read())

                super(YAMLCredentials, self).__init__(config['app_id'], config['app_secret'], config['app_token'], config['endpoint'])

except ImportError:
    # No YAML config adn credentials :(
    pass


class JSONEnvironmentFallbackConfig(Config):
    """
    This is the real hot shit.
    If a config value is not found in the JSON config, the given environment
    variable is used instead.

    :param jsonfile: The path to the json configuration file.

    .. code-block:: python

        # if the field *authorization* is not present in the config file,
        # then the environment variable *Api_AUTH* will be used for the
        # config variable authorization.
        conf = JSONEnvironmentFallbackConfig('myconf.json', authorization='Api_AUTH')
    """
    def __init__(self, jsonfile, **kwargs):
        with open(jsonfile) as cfgfile:
            self.data = json.load(cfgfile)

        for key, value in kwargs.items():
            if key not in Config.PARAMS:
                raise ApiException("unknown configuration key parameter")

            if key not in self.data:
                self.data[key] = os.environ[value]

        if "logging" in self.data and self.data["logging"] is not None:
            logging.config.dictConfig(self.data["logging"])

    def __getattr__(self, name):
        return self.data[name]
