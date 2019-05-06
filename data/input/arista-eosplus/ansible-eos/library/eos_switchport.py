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
module: eos_switchport
short_description: Manage switchport (layer 2) interface resources in EOS
description:
  - Provides active state management of switchport (layer 2) interface
    configuration in Arista EOS.  Logical switchports are mutually exclusive
    with M(eos_ipinterface).
version_added: 1.0.0
category: Bridging
author: Arista EOS+
requirements:
  - Arista EOS 4.13.7M or later with command API enabled
  - Python Client for eAPI 0.3.0 or later
notes:
  - All configuration is idempotent unless otherwise specified
  - Supports eos metaparameters for using the eAPI transport
  - Supports stateful resource configuration.
options:
  name:
    description:
      - The unique interface identifier name.  The interface name must use
        the full interface name (no abbreviated names).  For example,
        interfaces should be specified as Ethernet1 not Et1
    required: true
    default: null
    choices: []
    aliases: []
    version_added: 1.0.0
  mode:
    description:
      - Identifies the mode of operation for the interface.  Switchport
        interfaces can act as trunk interfaces (carrying multiple VLANs)
        or as access interfaces (attached to a single VLAN).  The EOS
        default value is 'access'
    required: false
    default: null
    choices: ['trunk', 'access']
    aliases: []
    version_added: 1.0.0
  access_vlan:
    description:
      - Configures the VLAN associated with a switchport that is
        configured to use 'access' mode.  This parameter only takes
        effect if mode is equal to 'access'.  Valid values for access
        vlan are in the range of 1 to 4094.  The EOS default value for
        access vlan is 1
    required: false
    default: null
    choices: []
    aliases: []
    version_added: 1.0.0
  trunk_native_vlan:
    description:
      - Configures the native VLAN on a trunk interface for untagged
        packets entering the switchport.  This parameter only takes
        effect if mode is equal to 'trunk'.  Valid values for trunk
        native vlan are in the range of 1 to 4094.  The EOS default value
        for trunk native value is 1.
    required: false
    default: null
    choices: []
    aliases: []
    version_added: 1.0.0
  trunk_allowed_vlans:
    description:
      - Configures the set of VLANs that are allowed to traverse this
        switchport interface.  This parameter only takes effect if
        the mode is configured to 'trunk'.  This parameter accepts a comma
        delimited list of VLAN IDs to configure on the trunk port.  Each
        VLAN ID must be in the valid range of 1 to 4094.  The EOS default
        value for trunk allowed vlans is 1-4094.
    required: false
    default: null
    choices: []
    aliases: []
    version_added: 1.0.0
  trunk_groups:
    description:
      - Configures the list of trunk groups on the switchport.  The parameter
        accepts a comma separated list of values to be provisioned on the
        interface.
    required: false
    default: null
    choices: []
    aliases: []
    version_added: 1.1.0
"""

EXAMPLES = """

- name: Ensure Ethernet1 is an access port
  eos_switchport: name=Ethernet1 mode=access access_vlan=10

- name: Ensure Ethernet12 is a trunk port
  eos_switchport: name=Ethernet12 mode=trunk trunk_native_vlan=100

- name: Add the set of allowed vlans to Ethernet2/1
  eos_switchport: name=Ethernet2/1 mode=trunk trunk_allowed_vlans=1,10,100

- name: Add trunk group values to an interface
  eos_switchport: name=Ethernet5 trunk_groups=foo,bar,baz

"""

from pyeapi.utils import expand_range
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

def sort_vlans(arg):
    """Converts the arg to a list and sorts the values
    """
    value = sorted([int(x) for x in arg.split(',')])
    value = [str(x) for x in value]
    return ','.join(value)

def instance(module):
    """ Returns switchport instance object properties
    """
    name = module.attributes['name']
    result = module.node.api('switchports').get(name)
    _instance = dict(name=name, state='absent')
    if result:
        _instance['state'] = 'present'
        _instance['mode'] = result['mode']
        _instance['access_vlan'] = result['access_vlan']
        _instance['trunk_native_vlan'] = result['trunk_native_vlan']
        vlans = ','.join(expand_range(result['trunk_allowed_vlans']))
        _instance['trunk_allowed_vlans'] = sort_vlans(vlans)
        _instance['trunk_groups'] = ','.join(result['trunk_groups'])
    return _instance

def create(module):
    """Creates a new instance of switchport on the node
    """
    name = module.attributes['name']
    module.log('Invoked create for eos_switchport[%s]' % name)
    module.node.api('switchports').create(name)

def remove(module):
    """Removes an existing instance of switchport on the node
    """
    name = module.attributes['name']
    module.log('Invoked remove for eos_switchport[%s]' % name)
    module.node.api('switchports').delete(name)

def set_mode(module):
    """Configures the mode attribute for the switchport
    """
    name = module.attributes['name']
    value = module.attributes['mode']
    module.log('Invoked set_mode for eos_switchport[%s] '
               'with value %s' % (name, value))
    module.node.api('switchports').set_mode(name, value)

def set_access_vlan(module):
    """Configures the access vlan attribute for the switchport
    """
    name = module.attributes['name']
    value = module.attributes['access_vlan']
    module.log('Invoked set_access_vlan for eos_switchport[%s] '
               'with value %s' % (name, value))
    module.node.api('switchports').set_access_vlan(name, value)

def set_trunk_native_vlan(module):
    """Configures the trunk native vlan attribute for the switchport
    """
    name = module.attributes['name']
    value = module.attributes['trunk_native_vlan']
    module.log('Invoked set_trunk_native_vlan for eos_switchport[%s] '
               'with value %s' % (name, value))
    module.node.api('switchports').set_trunk_native_vlan(name, value)

def set_trunk_allowed_vlans(module):
    """Configures the trunk allowed vlans attribute for the switchport
    """
    name = module.attributes['name']
    value = module.attributes['trunk_allowed_vlans']
    module.log('Invoked set_trunk_allowed_vlans for eos_switchport[%s] '
               'with value %s' % (name, value))
    module.node.api('switchports').set_trunk_allowed_vlans(name, value)

def set_trunk_groups(module):
    """Configures the set of trunk groups on the interface
    """
    name = module.attributes['name']
    value = module.attributes['trunk_groups'].split(',')
    module.log('Invoked set_trunk_groups for eos_switchport[%s] '
               'with value %s' % (name, value))
    module.node.api('switchports').set_trunk_groups(name, value)

def validate_trunk_groups(value):
    """Validates the trunk_groups argument
    """
    if not value:
        return None
    values = sorted(value.split(','))
    return ','.join(values)

def validate_trunk_allowed_vlans(value):
    """Validates the trunk_allowed_vlans argument
    """
    if not value:
        return None
    value = ','.join(expand_range(value))
    return sort_vlans(value)

def main():
    """ The main module routine called when the module is run by Ansible
    """

    argument_spec = dict(
        name=dict(required=True),
        mode=dict(choices=['access', 'trunk']),
        access_vlan=dict(),
        trunk_native_vlan=dict(),
        trunk_allowed_vlans=dict(),
        trunk_groups=dict()
    )

    module = EosAnsibleModule(argument_spec=argument_spec,
                              supports_check_mode=True)

    module.flush(True)

main()