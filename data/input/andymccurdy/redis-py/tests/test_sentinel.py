from __future__ import with_statement
import pytest

from redis import exceptions
from redis.sentinel import (Sentinel, SentinelConnectionPool,
                            MainNotFoundError, SubordinateNotFoundError)
from redis._compat import next
import redis.sentinel


class SentinelTestClient(object):
    def __init__(self, cluster, id):
        self.cluster = cluster
        self.id = id

    def sentinel_mains(self):
        self.cluster.connection_error_if_down(self)
        self.cluster.timeout_if_down(self)
        return {self.cluster.service_name: self.cluster.main}

    def sentinel_subordinates(self, main_name):
        self.cluster.connection_error_if_down(self)
        self.cluster.timeout_if_down(self)
        if main_name != self.cluster.service_name:
            return []
        return self.cluster.subordinates


class SentinelTestCluster(object):
    def __init__(self, service_name='mymain', ip='127.0.0.1', port=6379):
        self.clients = {}
        self.main = {
            'ip': ip,
            'port': port,
            'is_main': True,
            'is_sdown': False,
            'is_odown': False,
            'num-other-sentinels': 0,
        }
        self.service_name = service_name
        self.subordinates = []
        self.nodes_down = set()
        self.nodes_timeout = set()

    def connection_error_if_down(self, node):
        if node.id in self.nodes_down:
            raise exceptions.ConnectionError

    def timeout_if_down(self, node):
        if node.id in self.nodes_timeout:
            raise exceptions.TimeoutError

    def client(self, host, port, **kwargs):
        return SentinelTestClient(self, (host, port))


@pytest.fixture()
def cluster(request):
    def teardown():
        redis.sentinel.StrictRedis = saved_StrictRedis
    cluster = SentinelTestCluster()
    saved_StrictRedis = redis.sentinel.StrictRedis
    redis.sentinel.StrictRedis = cluster.client
    request.addfinalizer(teardown)
    return cluster


@pytest.fixture()
def sentinel(request, cluster):
    return Sentinel([('foo', 26379), ('bar', 26379)])


def test_discover_main(sentinel):
    address = sentinel.discover_main('mymain')
    assert address == ('127.0.0.1', 6379)


def test_discover_main_error(sentinel):
    with pytest.raises(MainNotFoundError):
        sentinel.discover_main('xxx')


def test_discover_main_sentinel_down(cluster, sentinel):
    # Put first sentinel 'foo' down
    cluster.nodes_down.add(('foo', 26379))
    address = sentinel.discover_main('mymain')
    assert address == ('127.0.0.1', 6379)
    # 'bar' is now first sentinel
    assert sentinel.sentinels[0].id == ('bar', 26379)


def test_discover_main_sentinel_timeout(cluster, sentinel):
    # Put first sentinel 'foo' down
    cluster.nodes_timeout.add(('foo', 26379))
    address = sentinel.discover_main('mymain')
    assert address == ('127.0.0.1', 6379)
    # 'bar' is now first sentinel
    assert sentinel.sentinels[0].id == ('bar', 26379)


def test_main_min_other_sentinels(cluster):
    sentinel = Sentinel([('foo', 26379)], min_other_sentinels=1)
    # min_other_sentinels
    with pytest.raises(MainNotFoundError):
        sentinel.discover_main('mymain')
    cluster.main['num-other-sentinels'] = 2
    address = sentinel.discover_main('mymain')
    assert address == ('127.0.0.1', 6379)


def test_main_odown(cluster, sentinel):
    cluster.main['is_odown'] = True
    with pytest.raises(MainNotFoundError):
        sentinel.discover_main('mymain')


def test_main_sdown(cluster, sentinel):
    cluster.main['is_sdown'] = True
    with pytest.raises(MainNotFoundError):
        sentinel.discover_main('mymain')


def test_discover_subordinates(cluster, sentinel):
    assert sentinel.discover_subordinates('mymain') == []

    cluster.subordinates = [
        {'ip': 'subordinate0', 'port': 1234, 'is_odown': False, 'is_sdown': False},
        {'ip': 'subordinate1', 'port': 1234, 'is_odown': False, 'is_sdown': False},
    ]
    assert sentinel.discover_subordinates('mymain') == [
        ('subordinate0', 1234), ('subordinate1', 1234)]

    # subordinate0 -> ODOWN
    cluster.subordinates[0]['is_odown'] = True
    assert sentinel.discover_subordinates('mymain') == [
        ('subordinate1', 1234)]

    # subordinate1 -> SDOWN
    cluster.subordinates[1]['is_sdown'] = True
    assert sentinel.discover_subordinates('mymain') == []

    cluster.subordinates[0]['is_odown'] = False
    cluster.subordinates[1]['is_sdown'] = False

    # node0 -> DOWN
    cluster.nodes_down.add(('foo', 26379))
    assert sentinel.discover_subordinates('mymain') == [
        ('subordinate0', 1234), ('subordinate1', 1234)]
    cluster.nodes_down.clear()

    # node0 -> TIMEOUT
    cluster.nodes_timeout.add(('foo', 26379))
    assert sentinel.discover_subordinates('mymain') == [
        ('subordinate0', 1234), ('subordinate1', 1234)]


def test_main_for(cluster, sentinel):
    main = sentinel.main_for('mymain', db=9)
    assert main.ping()
    assert main.connection_pool.main_address == ('127.0.0.1', 6379)

    # Use internal connection check
    main = sentinel.main_for('mymain', db=9, check_connection=True)
    assert main.ping()


def test_subordinate_for(cluster, sentinel):
    cluster.subordinates = [
        {'ip': '127.0.0.1', 'port': 6379,
         'is_odown': False, 'is_sdown': False},
    ]
    subordinate = sentinel.subordinate_for('mymain', db=9)
    assert subordinate.ping()


def test_subordinate_for_subordinate_not_found_error(cluster, sentinel):
    cluster.main['is_odown'] = True
    subordinate = sentinel.subordinate_for('mymain', db=9)
    with pytest.raises(SubordinateNotFoundError):
        subordinate.ping()


def test_subordinate_round_robin(cluster, sentinel):
    cluster.subordinates = [
        {'ip': 'subordinate0', 'port': 6379, 'is_odown': False, 'is_sdown': False},
        {'ip': 'subordinate1', 'port': 6379, 'is_odown': False, 'is_sdown': False},
    ]
    pool = SentinelConnectionPool('mymain', sentinel)
    rotator = pool.rotate_subordinates()
    assert next(rotator) in (('subordinate0', 6379), ('subordinate1', 6379))
    assert next(rotator) in (('subordinate0', 6379), ('subordinate1', 6379))
    # Fallback to main
    assert next(rotator) == ('127.0.0.1', 6379)
    with pytest.raises(SubordinateNotFoundError):
        next(rotator)
