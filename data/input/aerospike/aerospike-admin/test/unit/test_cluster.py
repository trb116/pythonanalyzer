# Copyright 2013-2016 Aerospike, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http:#www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from mock import patch, Mock
import unittest2 as unittest
from lib.cluster import Cluster
from lib.node import Node

class ClusterTest(unittest.TestCase):
    def getInfoMock(self, return_value):
        Node.info = mock.Mock()
        n = Node("127.0.0.1")
        return n

    def setUp(self):
        patcher = patch('lib.node.Node')
        self.addCleanup(patcher.stop)
        Node = patcher.start()

    def testInitCluster(self):
        pass
