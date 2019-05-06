#!/usr/bin/python
#
# Copyright (c) 2015, Arista Networks, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#   Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
#   Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
#
#   Neither the name of Arista Networks nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL ARISTA NETWORKS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
DOCUMENTATION = """
---
module: eos_vrrp
short_description: Manage EOS VRRP resources
description:
  - This module will manage VRRP configurations on EOS nodes
version_added: 1.2.0
category: VRRP
author: Arista EOS+
requirements:
  - Arista EOS 4.13.7M or later with command API enabled
  - Python Client for eAPI 0.4.0 or later
notes:
  - All configuration is idempotent unless otherwise specified
  - Supports eos metaparameters for using the eAPI transport
  - Supports stateful resource configuration.
options:
  interface:
    description:
      - The interface on which the VRRP is configured
    required: true
    default: null
    choices: []
    aliases: []
    version_added: 1.2.0
  vrid:
    description:
      - The unique identifying ID of the VRRP on its interface
    required: true
    default: null
    choices: []
    aliases: []
    version_added: 1.2.0
  enable:
    description:
      - The state of the VRRP
    required: false
    default: True
    choices: [True, False]
    aliases: []
    version_added: 1.2.0
  primary_ip:
    description:
      - The ip address of the virtual router
    required: false
    default: '0.0.0.0'
    choices: []
    aliases: []
    version_added: 1.2.0
  priority:
    description:
      - The priority setting for the virtual router
    required: false
    default: 100
    choices: []
    aliases: []
    version_added: 1.2.0
  description:
    description:
      - Text description of the virtual router
    required: false
    default: null
    choices: []
    aliases: []
    version_added: 1.2.0
  ip_version:
    description:
      - VRRP version in place on the virtual router
    required: false
    default: 2
    choices: [2, 3]
    aliases: []
    version_added: 1.2.0
  secondary_ip:
    description:
      - Array of secondary ip addresses assigned to the VRRP
    required: false
    default: []
    choices: []
    aliases: []
    version_added: 1.2.0
  timers_advertise:
    description:
      - Interval between advertisement messages to virtual router group
    required: false
    default: 1
    choices: []
    aliases: []
    version_added: 1.2.0
  preempt:
    description:
      - Preempt mode setting for the virtual router
    required: false
    default: True
    choices: [True, False]
    aliases: []
    version_added: 1.2.0
  preempt_delay_min:
    description:
      - Interval between a preempt event and takeover
    required: false
    default: 0
    choices: []
    aliases: []
    version_added: 1.2.0
  preempt_delay_reload:
    description:
      - Interval between a preempt event and takeover after reload
    required: false
    default: 0
    choices: []
    aliases: []
    version_added: 1.2.0
  delay_reload:
    description:
      - Delay between switch reload and VRRP initialization
    required: false
    default: 0
    choices: []
    aliases: []
    version_added: 1.2.0
  mac_addr_adv_interval:
    description:
      - Interval between advertisement messages to virtual router group
    required: false
    default: 30
    choices: []
    aliases: []
    version_added: 1.2.0
  track:
    description:
      - Array of track definitions to be assigned to the vrrp
    required: false
    default: []
    choices: []
    aliases: []
    version_added: 1.2.0
"""

EXAMPLES = """

# Configure the set of tracked objects for the VRRP
# Create a list of dictionaries, where name is the object to be
# tracked, action is shutdown or decrement, and amount is the
# decrement amount. Amount is not specified when action is shutdown.

vars:
  tracks:
      - name: Ethernet1
        action: shutdown
      - name: Ethernet2
        action: decrement
        amount: 5

# Setup the VRRP

  - eos_vrrp:
      interface=Vlan70
      vrid=10
      enable=True
      primary_ip=10.10.10.1
      priority=50
      description='vrrp 10 on Vlan70'
      ip_version=2
      secondary_ip=['10.10.10.70','10.10.10.80']
      timers_advertise=15
      preempt=True
      preempt_delay_min=30
      preempt_delay_reload=30
      delay_reload=30
      track="{{ tracks }}"

"""
import yaml
#<<EOS_COMMON_MODULE_START>>

import syslog
import collections

from ansible.module_utils.basic import *

try:
    import pyeapi
    PYEAPI_AVAILABLE = True
except ImportError:
    PYEAPI_AVAILABLE = False

DEFAULT_SYSLOG_PRIORITY = syslog.LOG_NOTICE
DEFAULT_CONNECTION = 'localhost'
TRANSPORTS = ['socket', 'http', 'https', 'http_local']

class EosConnection(object):

    __attributes__ = ['username', 'password', 'host', 'transport', 'port']

    def __init__(self, **kwargs):
        self.connection = kwargs['connection']
        self.transport = kwargs.get('transport')

        self.username = kwargs.get('username')
        self.password = kwargs.get('password')

        self.host = kwargs.get('host')
        self.port = kwargs.get('port')

        self.config = kwargs.get('config')

    def connect(self):
        if self.config is not None:
            pyeapi.load_config(self.config)

        config = dict()

        if self.connection is not None:
            config = pyeapi.config_for(self.connection)
            if not config:
                msg = 'Connection name "{}" not found'.format(self.connection)

        for key in self.__attributes__:
            if getattr(self, key) is not None:
                config[key] = getattr(self, key)

        if 'transport' not in config:
            raise ValueError('Connection must define a transport')

        connection = pyeapi.client.make_connection(**config)
        node = pyeapi.client.Node(connection, **config)

        try:
            node.enable('show version')
        except (pyeapi.eapilib.ConnectionError, pyeapi.eapilib.CommandError):
            raise ValueError('unable to connect to {}'.format(node))
        return node


class EosAnsibleModule(AnsibleModule):

    meta_args = {
        'config': dict(),
        'username': dict(),
        'password': dict(),
        'host': dict(),
        'connection': dict(default=DEFAULT_CONNECTION),
        'transport': dict(choices=TRANSPORTS),
        'port': dict(),
        'debug': dict(type='bool', default='false'),
        'logging': dict(type='bool', default='true')
    }

    stateful_args = {
        'state': dict(default='present', choices=['present', 'absent']),
    }

    def __init__(self, stateful=True, autorefresh=False, *args, **kwargs):

        kwargs['argument_spec'].update(self.meta_args)

        self._stateful = stateful
        if stateful:
            kwargs['argument_spec'].update(self.stateful_args)

        ## Ok, so in Ansible 2.0,
        ## AnsibleModule.__init__() sets self.params and then
        ##   calls self.log()
        ##   (through self._log_invocation())
        ##
        ## However, self.log() (overridden in EosAnsibleModule)
        ##   references self._logging
        ## and self._logging (defined in EosAnsibleModule)
        ##   references self.params.
        ##
        ## So ... I'm defining self._logging without "or self.params['logging']"
        ##   *before* AnsibleModule.__init__() to avoid a "ref before def".
        ##
        ## I verified that this works with Ansible 1.9.4 and 2.0.0.2.
        ## The only caveat is that the first log message in
        ##   AnsibleModule.__init__() won't be subject to the value of
        ##   self.params['logging'].
        self._logging = kwargs.get('logging')
        super(EosAnsibleModule, self).__init__(*args, **kwargs)

        self.result = dict(changed=False, changes=dict())

        self._debug = kwargs.get('debug') or self.boolean(self.params['debug'])
        self._logging = kwargs.get('logging') or self.params['logging']

        self.log('DEBUG flag is %s' % self._debug)

        self.debug('pyeapi_version', self.check_pyeapi())
        self.debug('stateful', self._stateful)
        self.debug('params', self.params)

        self._attributes = self.map_argument_spec()
        self.validate()
        self._autorefresh = autorefresh
        self._node = EosConnection(**self.params)
        self._node.connect()

        self._node = self.connect()
        self._instance = None

        self.desired_state = self.params['state'] if self._stateful else None
        self.exit_after_flush = kwargs.get('exit_after_flush')

    @property
    def instance(self):
        if self._instance:
            return self._instance

        func = self.func('instance')
        if not func:
            self.fail('Module does not support "instance"')

        try:
            self._instance = func(self)
        except Exception as exc:
            self.fail('instance[error]: %s' % exc.message)

        self.log("called instance: %s" % self._instance)
        return self._instance

    @property
    def attributes(self):
        return self._attributes

    @property
    def node(self):
        return self._node

    def check_pyeapi(self):
        if not PYEAPI_AVAILABLE:
            self.fail('Unable to import pyeapi, is it installed?')
        return pyeapi.__version__

    def map_argument_spec(self):
        """map_argument_spec maps only the module argument spec to attrs

        This method will map the argumentspec minus the meta_args to attrs
        and return the attrs.  This returns a dict object that includes only
        the original argspec plus the stateful_args (if self._stateful=True)

        Returns:
            dict: Returns a dict object that includes the original
                argument_spec plus stateful_args with values minus meta_args

        """
        keys = set(self.params).difference(self.meta_args)
        attrs = dict()
        attrs = dict([(k, self.params[k]) for k in self.params if k in keys])
        if 'CHECKMODE' in attrs:
            del attrs['CHECKMODE']
        return attrs

    def validate(self):
        for key, value in self.attributes.iteritems():
            func = self.func('validate_%s' % key)
            if func:
                self.attributes[key] = func(value)

    def create(self):
        if not self.check_mode:
            func = self.func('create')
            if not func:
                self.fail('Module must define "create" function')
            return self.invoke(func, self)

    def remove(self):
        if not self.check_mode:
            func = self.func('remove')
            if not func:
                self.fail('Module most define "remove" function')
            return self.invoke(func, self)

    def flush(self, exit_after_flush=False):
        self.exit_after_flush = exit_after_flush

        if self.desired_state == 'present' or not self._stateful:
            if self.instance.get('state') == 'absent':
                changed = self.create()
                self.result['changed'] = changed or True
                self.refresh()
                # After a create command, flush the running-config
                # so we get the latest for any other attributes
                self._node._running_config = None

            changeset = self.attributes.viewitems() - self.instance.viewitems()

            if self._debug:
                self.debug('desired_state', self.attributes)
                self.debug('current_state', self.instance)

            changes = self.update(changeset)
            if changes:
                self.result['changes'] = changes
                self.result['changed'] = True

            self._attributes.update(changes)

            flush = self.func('flush')
            if flush:
                self.invoke(flush, self)

        elif self.desired_state == 'absent' and self._stateful:
            if self.instance.get('state') == 'present':
                changed = self.remove()
                self.result['changed'] = changed or True

        elif self._stateful:
            if self.desired_state != self.instance.get('state'):
                func = self.func(self.desired_state)
                changed = self.invoke(func, self)
                self.result['changed'] = changed or True

        self.refresh()
        # By calling self.instance here we trigger another show running-config
        # all which causes delay.  Only if debug is enabled do we call this
        # since it will display the latest state of the object.
        if self._debug:
            self.result['instance'] = self.instance

        if self.exit_after_flush:
            self.exit()

    def update(self, changeset):
        changes = dict()
        for key, value in changeset:
            if value is not None:
                changes[key] = value
                func = self.func('set_%s' % key)
                if func and not self.check_mode:
                    try:
                        self.invoke(func, self)
                    except Exception as exc:
                        self.fail(exc.message)
        return changes

    def connect(self):
        if self.params['config']:
            pyeapi.load_config(self.params['config'])

        config = dict()

        if self.params['connection']:
            config = pyeapi.config_for(self.params['connection'])
            if not config:
                msg = 'Connection name "%s" not found' % self.params['connection']
                self.fail(msg)

        if self.params['username']:
            config['username'] = self.params['username']

        if self.params['password']:
            config['password'] = self.params['password']

        if self.params['transport']:
            config['transport'] = self.params['transport']

        if self.params['port']:
            config['port'] = self.params['port']

        if self.params['host']:
            config['host'] = self.params['host']

        if 'transport' not in config:
            self.fail('Connection must define a transport')

        connection = pyeapi.client.make_connection(**config)
        self.log('Creating connection with autorefresh=%s' % self._autorefresh)
        node = pyeapi.client.Node(connection, autorefresh=self._autorefresh,
                                  **config)

        try:
            resp = node.enable('show version')
            self.debug('eos_version', resp[0]['result']['version'])
            self.debug('eos_model', resp[0]['result']['modelName'])
        except (pyeapi.eapilib.ConnectionError, pyeapi.eapilib.CommandError):
            self.fail('unable to connect to %s' % node)
        else:
            self.log('Connected to node %s' % node)
            self.debug('node', str(node))

        return node

    def config(self, commands):
        self.result['changed'] = True
        if not self.check_mode:
            self.node.config(commands)

    def api(self, module):
        return self.node.api(module)

    def func(self, name):
        return globals().get(name)

    def invoke(self, func, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            self.fail(exc.message)

    def invoke_function(self, name, *args, **kwargs):
        func = self.func(name)
        if func:
            return self.invoke(func, *args, **kwargs)

    def fail(self, msg):
        self.invoke_function('on_fail', self)
        self.log('ERROR: %s' % msg, syslog.LOG_ERR)
        self.fail_json(msg=msg)

    def exit(self):
        self.invoke_function('on_exit', self)
        self.log('Module completed successfully')
        self.exit_json(**self.result)

    def refresh(self):
        self._instance = None

    def debug(self, key, value):
        if self._debug:
            if 'debug' not in self.result:
                self.result['debug'] = dict()
            self.result['debug'][key] = value

    def log(self, message, log_args=None, priority=None):
        if self._logging:
            syslog.openlog('ansible-eos')
            priority = priority or DEFAULT_SYSLOG_PRIORITY
            syslog.syslog(priority, str(message))

    @classmethod
    def add_state(cls, name):
        cls.stateful_args['state']['choices'].append(name)

#<<EOS_COMMON_MODULE_END>>

def instance(module):
    """ Returns an instance of Vrrp based on interface and vrid
    """
    interface = module.attributes['interface']
    vrid = module.attributes['vrid']
    _instance = dict(interface=interface, vrid=vrid, state='absent')

    try:
        result = module.node.api('vrrp').get(interface)[vrid]
    except:
        result = None

    if result:
        _instance['state'] = 'present'

        _instance['enable'] = result['enable']
        _instance['primary_ip'] = result['primary_ip']
        _instance['priority'] = str(result['priority'])
        _instance['description'] = result['description']
        _instance['ip_version'] = str(result['ip_version'])
        _instance['secondary_ip'] = yaml.dump(sorted(result['secondary_ip']))
        _instance['timers_advertise'] = str(result['timers_advertise'])
        _instance['preempt'] = result['preempt']
        _instance['preempt_delay_min'] = str(result['preempt_delay_min'])
        _instance['preempt_delay_reload'] = str(result['preempt_delay_reload'])
        _instance['delay_reload'] = str(result['delay_reload'])
        _instance['mac_addr_adv_interval'] = \
            str(result['mac_addr_adv_interval'])
        _instance['track'] = yaml.dump(sorted(result['track']))
    return _instance


def create(module):
    """Creates a vrrp on the interface
    """
    interface = module.attributes['interface']
    vrid = module.attributes['vrid']
    module.node.api('vrrp').create(interface, vrid)


def remove(module):
    """Removes a vrrp configuration from the interface
    """
    interface = module.attributes['interface']
    vrid = module.attributes['vrid']
    module.node.api('vrrp').delete(interface, vrid)


def set_enable(module):
    """Configures the enable attribute for the vrrp.
    """
    interface = module.attributes['interface']
    vrid = module.attributes['vrid']
    value = module.attributes['enable']
    module.node.api('vrrp').set_enable(interface, vrid, value=value)


def set_primary_ip(module):
    """Configures the primary ip attribute for the vrrp.
    """
    interface = module.attributes['interface']
    vrid = module.attributes['vrid']
    value = module.attributes['primary_ip']
    module.node.api('vrrp').set_primary_ip(interface, vrid, value=value)


def set_priority(module):
    """Configures the priority attribute for the vrrp
    """
    interface = module.attributes['interface']
    vrid = module.attributes['vrid']
    value = module.attributes['priority']
    if not value.isdigit():
        raise ValueError("vrrp argument 'priority' must be an integer")
    module.node.api('vrrp').set_priority(interface, vrid, value=int(value))


def set_description(module):
    """Configures the description attribute for the vrrp
    """
    interface = module.attributes['interface']
    vrid = module.attributes['vrid']
    value = module.attributes['description']
    if value == '':
        # Empty string passed in - disable description on the vrrp
        module.node.api('vrrp').set_description(interface, vrid, disable=True)
    else:
        module.node.api('vrrp').set_description(interface, vrid, value=value)


def set_ip_version(module):
    """Configures the ip version attribute for the vrrp
    """
    interface = module.attributes['interface']
    vrid = module.attributes['vrid']
    value = module.attributes['ip_version']
    if not value.isdigit():
        raise ValueError("vrrp argument 'ip_version' must be an integer")
    module.node.api('vrrp').set_ip_version(interface, vrid, value=int(value))


def validate_secondary_ip(value):
    """Converts the secondary ip array argument into a string that is
    matchable in ansible-eos. The array is sorted before conversion so
    matching is exact.
    """
    if value is None:
        return None

    # If value string is not surrounded by brackets as
    # a list, add the brackets
    if not re.match(r'^\[.*\]$', value):
        value = "[%s]" % value

    # Convert the string to an object, sort, and convert
    # back to string for matching
    newval = sorted(yaml.load(value))
    newstr = yaml.dump(newval)

    return newstr


def set_secondary_ip(module):
    """Configures the secondary ip attribute for the vrrp
    """
    interface = module.attributes['interface']
    vrid = module.attributes['vrid']
    value = module.attributes['secondary_ip']
    if value == '':
        value = []
    else:
        value = yaml.load(value)
    module.node.api('vrrp').set_secondary_ips(interface, vrid, value)


def set_timers_advertise(module):
    """Configures the timers advertise attribute for the vrrp
    """
    interface = module.attributes['interface']
    vrid = module.attributes['vrid']
    value = module.attributes['timers_advertise']
    if not value.isdigit():
        raise ValueError("vrrp argument 'timers_advertise' must be an integer")
    module.node.api('vrrp').set_timers_advertise(interface, vrid,
                                                 value=int(value))


def set_preempt(module):
    """Configures the preempt attribute for the vrrp.
    """
    interface = module.attributes['interface']
    vrid = module.attributes['vrid']
    value = module.attributes['preempt']
    module.node.api('vrrp').set_preempt(interface, vrid, value=value)


def set_preempt_delay_min(module):
    """Configures the preempt delay minimum attribute for the vrrp
    """
    interface = module.attributes['interface']
    vrid = module.attributes['vrid']
    value = module.attributes['preempt_delay_min']
    if not value.isdigit():
        raise ValueError("vrrp argument 'preempt_delay_min' must "
                         "be an integer")
    module.node.api('vrrp').set_preempt_delay_min(interface, vrid,
                                                  value=int(value))


def set_preempt_delay_reload(module):
    """Configures the preempt delay reload attribute for the vrrp
    """
    interface = module.attributes['interface']
    vrid = module.attributes['vrid']
    value = module.attributes['preempt_delay_reload']
    if not value.isdigit():
        raise ValueError("vrrp argument 'preempt_delay_reload' must "
                         "be an integer")
    module.node.api('vrrp').set_preempt_delay_reload(interface, vrid,
                                                     value=int(value))


def set_delay_reload(module):
    """Configures the delay reload attribute for the vrrp
    """
    interface = module.attributes['interface']
    vrid = module.attributes['vrid']
    value = module.attributes['delay_reload']
    if not value.isdigit():
        raise ValueError("vrrp argument 'delay_reload' must "
                         "be an integer")
    module.node.api('vrrp').set_delay_reload(interface, vrid,
                                             value=int(value))


def set_mac_addr_adv_interval(module):
    """Configures the mac-address advertisement-interval attribute for the vrrp
    """
    interface = module.attributes['interface']
    vrid = module.attributes['vrid']
    value = module.attributes['mac_addr_adv_interval']
    if not value.isdigit():
        raise ValueError("vrrp argument 'mac_addr_adv_interval' must "
                         "be an integer")
    module.node.api('vrrp').set_mac_addr_adv_interval(interface, vrid,
                                                      value=int(value))


def validate_track(value):
    """Converts the tracked object array argument into a string that is
    matchable in ansible-eos. The array is sorted before conversion so
    matching is exact.
    """
    if value is None:
        return None

    # If value string is not surrounded by brackets as
    # a list, add the brackets
    if not re.match(r'^\[.*\]$', value):
        value = "[%s]" % value

    # Convert the string to an object, sort, and convert
    # back to string for matching
    newval = sorted(yaml.load(value))
    newstr = yaml.dump(newval)

    return newstr


def set_track(module):
    """Configures the track attributes for the vrrp

    Takes the tracks definition string used by eos_vrrp and converts it
    to a dictionary for the set_tracks method of pyeapi.
    """
    interface = module.attributes['interface']
    vrid = module.attributes['vrid']
    value = module.attributes['track']
    if value == '':
        value = []
    else:
        value = yaml.load(value)

    module.node.api('vrrp').set_tracks(interface, vrid, value)


def main():
    """ The main module routine called when the module is run by Ansible
    """

    argument_spec = dict(
        interface=dict(required=True),
        vrid=dict(required=True, type='int'),
        enable=dict(type='bool', default=True),
        primary_ip=dict(default='0.0.0.0'),
        priority=dict(default='100'),
        description=dict(),
        secondary_ip=dict(default=''),
        ip_version=dict(default='2'),
        timers_advertise=dict(default='1'),
        mac_addr_adv_interval=dict(default='30'),
        preempt=dict(type='bool', default=True),
        preempt_delay_min=dict(default='0'),
        preempt_delay_reload=dict(default='0'),
        delay_reload=dict(default='0'),
        authentication_type=dict(),
        track=dict(default=''),
    )

    argument_spec['continue'] = dict()

    module = EosAnsibleModule(argument_spec=argument_spec,
                              supports_check_mode=True)

    module.flush(True)

main()