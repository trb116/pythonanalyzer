import os
from . import FSQTestCase
from .internal import test_type_own_mode, normalize
from .constants import ROOT1, ROOT2, NON_ASCII, NOT_NORMAL, ILLEGAL_NAMES,\
                       ILLEGAL_MODE, ILLEGAL_NAME, ILLEGAL_UID,\
                       ILLEGAL_UNAME, ORIG_QUEUE_UG, ORIG_ITEM_UG, MODES,\
                       UID, GID, UNAME, GNAME, NOROOT
# FROM PAPA-BEAR IMPORT THE FOLLOWING
from .. import install, uninstall, constants as _c, FSQPathError,\
               FSQInstallError, FSQCoerceError, FSQConfigError

def _valid_uninstall(queue):
    dirs = os.listdir(_c.FSQ_ROOT)
    for d in dirs:
        if d == queue:
            return False
    return True

def _valid_install(queue, is_down=None, is_triggered=None, user=None,
                   group=None, mode=None, item_user=None, item_group=None,
                   item_mode=None):
    dirs = os.listdir(os.path.join(_c.FSQ_ROOT, queue))
    seen = []
    allowed = set([ _c.FSQ_FAIL, _c.FSQ_TMP, _c.FSQ_DONE, _c.FSQ_QUEUE, ])
    if is_down:
        allowed = allowed|set([ _c.FSQ_DOWN, ])
    if is_triggered:
        allowed = allowed|set([ _c.FSQ_TRIGGER, ])
    for d in dirs:
        if d in allowed:
            seen.append(d)
            t_path = os.path.join(_c.FSQ_ROOT, queue, d)
            st = os.stat(t_path)
            # tests for directory install
            if d not in ( _c.FSQ_DOWN, _c.FSQ_TRIGGER ):
                if _c.FSQ_QUEUE_USER != ORIG_QUEUE_UG[0]:
                    user = 1
                if _c.FSQ_QUEUE_GROUP != ORIG_QUEUE_UG[1]:
                    group = 1
                test_type_own_mode(st, t_path, 'd',
                                   user if user is None else UID,
                                   group if group is None else GID, mode)
            else:
                f_type = 'f'
                # is it a FIFO (man 2 stat)
                if d == _c.FSQ_TRIGGER:
                    f_type = 'p'
                if _c.FSQ_ITEM_USER != ORIG_ITEM_UG[0]:
                    user = 1
                if _c.FSQ_ITEM_GROUP != ORIG_ITEM_UG[1]:
                    group = 1
                test_type_own_mode(st, t_path, f_type,
                    item_user if item_user is None else UID,
                    item_group if item_group is None else GID, item_mode)
        else:
            raise ValueError('illegal entry: {0}; install failed'.format(d))
    if len(set(seen)^allowed):
        raise ValueError('missing entries: {0}; install'\
                         ' failed'.format(set(seen)^allowed))
    return True


class TestInstallUninstall(FSQTestCase):
    def _cycle(self, queue=None, **kwargs):
        uninstall_kwargs = {
            'item_user': kwargs.get('item_user', None),
            'item_group': kwargs.get('item_group', None),
            'item_mode': kwargs.get('item_mode', None)
        }
        queue = self._install(queue, **kwargs)
        self._uninstall(queue, **uninstall_kwargs)
        return queue

    def _install(self, queue=None, **kwargs):
        if queue is None:
            queue = normalize()
        install(queue, **kwargs)
        self.assertTrue(_valid_install(queue, **kwargs))
        return queue

    def _uninstall(self, queue, **kwargs):
        uninstall(queue, **kwargs)
        self.assertTrue(_valid_uninstall(queue))

    def test_basic(self):
        '''Test all permutations of arguments, or most of them anyway,
           combined with permuatations of module constants values.'''
        for root in ROOT1, ROOT2:
            _c.FSQ_ROOT = root
            # kwargsless install to root
            self._cycle()

            for down in True, False:
                # no is_triggered kwarg
                self._cycle(is_down=down)

                for is_t in True, False:
                    # no down kwarg
                    self._cycle(is_triggered=is_t)

                    # standard install -- all kwargs
                    self._cycle(is_down=down, is_triggered=is_t)

                    # change things up
                    queue = normalize()
                    _c.FSQ_QUEUE, _c.FSQ_TMP, _c.FSQ_DONE,\
                                 _c.FSQ_FAIL, _c.FSQ_DOWN = NOT_NORMAL
                    self._cycle(queue, is_down=down, is_triggered=is_t)

                    # test unicodeness
                    queue = normalize()
                    _c.FSQ_TMP = NON_ASCII
                    self._cycle(queue, is_down=down, is_triggered=is_t)
                # END is_triggered LOOP
            # END down LOOP
        # END ROOT loop

    def test_collide(self):
        '''Test installing to an already installed path.'''
        for root in ROOT1, ROOT2:
            _c.FSQ_ROOT = root
            queue = self._install()
            self.assertRaises(FSQInstallError, install, queue)
            self._uninstall(queue)

    def test_invalroot(self):
        '''Test install/uninstall to/from a non-existant FSQ_ROOT'''
        queue = normalize()
        _c.FSQ_ROOT = NOROOT
        self.assertRaises(FSQInstallError, install, queue)
        self.assertRaises(FSQInstallError, uninstall, queue)


    def test_invalnames(self):
        '''Test installing with illegal names'''
        for root in ROOT1, ROOT2:
            _c.FSQ_ROOT = root
            # verify installing queue with non-coercable name fails
            normalize()
            self.assertRaises(FSQCoerceError, install, ILLEGAL_NAME)
            self.assertRaises((OSError, AttributeError,), _valid_install,
                              ILLEGAL_NAME)
            for name in ILLEGAL_NAMES:
                normalize()
                self.assertRaises(FSQPathError, install, name)
                # verify that the queue doesn't exist
                self.assertRaises((OSError,ValueError,), _valid_install, name)
                for other in ('FSQ_QUEUE', 'FSQ_TMP', 'FSQ_FAIL', 'FSQ_DOWN',
                              'FSQ_TRIGGER'):
                    queue = normalize()
                    setattr(_c, other, name)
                    # verify path error
                    self.assertRaises(FSQPathError, install, queue,
                                      is_down=True, is_triggered=True)
                    # verify not installed
                    self.assertRaises(OSError, _valid_install, queue,
                                      is_down=True, is_triggered=True)

                    # verify non-string CoerceErrors
                    queue = normalize()
                    setattr(_c, other, ILLEGAL_NAME)
                    self.assertRaises(FSQCoerceError, install, queue,
                                      is_down=True, is_triggered=True)
                    self.assertRaises((OSError, ValueError,), _valid_install,
                                      queue, is_down=True, is_triggered=True)

    def test_usergroup(self):
        '''Test installing with queue user|group for tmp/done/fail/queue'''
        for uid, gid in ((UID, GID, ), (UNAME, GNAME, )):
            for root in ROOT1, ROOT2:
                _c.FSQ_ROOT = root
                # test only user kwarg
                self._cycle(user=uid)

                # test only group kwarg
                self._cycle(group=gid)

                # test with uid/gid passed in
                self._cycle(user=uid, group=gid)

                # test with uid/gid set
                queue = normalize()
                _c.FSQ_QUEUE_USER, _c.FSQ_QUEUE_GROUP = ( uid, gid, )
                self._cycle(queue)

                # plays well with other flags?
                for down in True, False:
                    for is_t in True, False:
                        self._cycle(user=uid, group=gid, is_down=down,
                                    is_triggered=is_t)
                    #END is_triggered LOOP
                # END down LOOP
            # END root LOOP

            # test illegal user id/group id
            queue = normalize()
            uid = gid = ILLEGAL_UID
            self.assertRaises(FSQInstallError, install, queue, user=uid)
            self.assertRaises(OSError, _valid_install, queue, user=uid)
            self.assertRaises(FSQInstallError, install, queue, group=gid)
            self.assertRaises(OSError, _valid_install, queue, group=gid)
            self.assertRaises(FSQInstallError, install, queue, user=uid,
                              group=gid)
            self.assertRaises(OSError, _valid_install, queue, user=uid,
                              group=gid)

            # test illegal group name/user name
            queue = normalize()
            uid = gid = ILLEGAL_UNAME
            self.assertRaises(TypeError, install, queue, user=uid)
            self.assertRaises((OSError, AttributeError,), _valid_install,
                              queue, user=uid)
            self.assertRaises(TypeError, install, queue, group=gid)
            self.assertRaises((OSError, AttributeError,), _valid_install,
                              queue, group=gid)
            self.assertRaises(TypeError, install, queue, user=uid,
                              group=gid)
            self.assertRaises((OSError, AttributeError,), _valid_install,
                              queue, user=uid, group=gid)
        # END uid,gid loop

    def test_itemusergroup(self):
        '''Test installing with item user|group for down/trigger-s'''
        for uid, gid in ((UID, GID, ), (UNAME, GNAME, )):
            for root in ROOT1, ROOT2:
                _c.FSQ_ROOT = root
                # test only user kwarg
                self._cycle(item_user=uid)

                # test only group kwarg
                self._cycle(item_group=gid)

                # test with uid/gid passed in
                self._cycle(item_user=uid, item_group=gid)

                # test with uid/gid set
                queue = normalize()
                _c.FSQ_ITEM_USER, _c.FSQ_ITEM_GROUP = ( uid, gid, )
                self._cycle()

                # plays well with other flags?
                for down in True, False:
                    self._cycle(item_user=uid, is_down=down)
                    self._cycle(item_group=gid, is_down=down)
                    self._cycle(item_user=uid, item_group=gid, is_down=down)
                    for is_t in True, False:
                        self._cycle(item_user=uid, is_triggered=is_t)
                        self._cycle(item_group=gid, is_triggered=is_t)
                        self._cycle(item_user=uid, item_group=gid,
                                    is_triggered=is_t)
                        self._cycle(item_user=uid, item_group=gid,
                                    is_triggered=is_t, is_down=down)
                        for quid, qgid in ((UID, GID,), (UNAME, GNAME,)):
                            self._cycle(item_user=uid, user=quid)
                            self._cycle(item_user=uid, group=qgid)
                            self._cycle(item_user=uid, user=quid, group=qgid)
                            self._cycle(item_group=gid, user=quid)
                            self._cycle(item_group=gid, group=qgid)
                            self._cycle(item_group=gid, user=quid, group=qgid)
                            self._cycle(item_user=uid, item_group=gid,
                                        user=quid)
                            self._cycle(item_user=uid, item_group=gid,
                                        group=qgid)
                            self._cycle(item_user=uid, item_group=gid,
                                        user=quid, group=qgid)
                            self._cycle(item_user=uid, item_group=gid,
                                        is_down=down, is_triggered=is_t,
                                        user=quid, group=qgid)
                        # END queue uid/gid LOOP
                    # END is_triggered LOOP
                # END down LOOP
            # END root LOOP
            for uid, gid in ((ILLEGAL_UID, ILLEGAL_UID,),
                            (ILLEGAL_UNAME, ILLEGAL_UNAME,)):
                queue = normalize()
                uid = gid = ILLEGAL_UID
                self.assertRaises(FSQConfigError, install, queue,
                                  item_user=uid, is_down=True)
                self.assertRaises((OSError, AttributeError,), _valid_install,
                                  queue, item_user=uid, is_down=True)
                self.assertRaises(FSQConfigError, install, queue,
                                  item_group=gid, is_down=True)
                self.assertRaises((OSError, AttributeError,),  _valid_install,
                                  queue, item_group=gid, is_down=True)
                self.assertRaises(FSQConfigError, install, queue,
                                  item_user=uid, item_group=gid, is_down=True)
                self.assertRaises((OSError, AttributeError,), _valid_install,
                                  queue, item_user=uid, item_group=gid,
                                  is_down=True)

                # verify install with illegal works, and uninstall fails
                queue = self._install(item_user=uid)
                self.assertRaises(FSQConfigError, uninstall, queue,
                                  item_user=uid)
                self.assertFalse(os.path.exists(os.path.join(root, queue,
                                 _c.FSQ_DOWN)))
                queue = self._install(item_group=gid)
                self.assertRaises(FSQConfigError, uninstall, queue,
                                  item_group=gid)
                self.assertFalse(os.path.exists(os.path.join(root, queue,
                                 _c.FSQ_DOWN)))
                queue = self._install(item_user=uid, item_group=gid)
                self.assertRaises(FSQConfigError, uninstall, queue,
                                  item_user=uid, item_group=gid)
                self.assertFalse(os.path.exists(os.path.join(root, queue,
                                 _c.FSQ_DOWN)))
            # END ILLEGAL LOOP
        # END uid,gid loop

    def test_mode(self):
        '''Test installing with queue modes for tmp/done/fail/queue'''
        for mode in MODES:
            for root in ROOT1, ROOT2:
                _c.FSQ_ROOT = root
                # test only mode kwarg
                self._cycle(mode=mode)

                # test with mode set
                queue = normalize()
                _c.FSQ_QUEUE_MODE = mode
                self._cycle(queue)

                # plays well with other flags?
                for down in True, False:
                    for is_t in True, False:
                        for uid, gid in ((UID, GID,), (UNAME, GNAME,)):
                            for quid, qgid in ((UID, GID,), (UNAME, GNAME,)):
                                self._cycle(mode=mode, is_down=down,
                                            is_triggered=is_t, user=quid,
                                            group=qgid, item_user=uid,
                                            item_group=gid)
                            # END queue uid/gid LOOP
                        # END uid,gid loop
                    # END is_triggered LOOP
                # END down LOOP
            # END root LOOP
            queue = normalize()
            mode = ILLEGAL_MODE
            self.assertRaises(TypeError, install, queue, mode=mode)
            self.assertRaises(OSError, _valid_install, queue, mode=mode)
        # END mode LOOP

    def test_itemmode(self):
        '''Test installing with item modes for down/trigger-s'''
        for mode in MODES:
            for root in ROOT1, ROOT2:
                _c.FSQ_ROOT = root
                # test only mode kwarg
                self._cycle(item_mode=mode)

                # test with mode set
                queue = normalize()
                _c.FSQ_ITEM_MODE = mode
                self._cycle(queue)

                # plays well with other flags?
                for down in True, False:
                    for is_t in True, False:
                        for uid, gid in ((UID, GID,), (UNAME, GNAME,)):
                            for quid, qgid in ((UID, GID,), (UNAME, GNAME,)):
                                for qm in MODES:
                                    self._cycle(item_mode=mode, mode=qm,
                                                is_down=down, user=quid,
                                                is_triggered=is_t,
                                                group=qgid, item_user=uid,
                                                item_group=gid)
                            # END queue uid/gid LOOP
                        # END uid,gid loop
                    # END is_triggered LOOP
                # END down LOOP
            # END root LOOP
            queue = normalize()
            mode = ILLEGAL_MODE
            self.assertRaises(TypeError, install, queue, item_mode=mode,
                              is_down=True)
            self.assertRaises(OSError, _valid_install, queue, item_mode=mode,
                              is_down=True)
            queue = self._install(item_mode=mode)
            self.assertRaises(TypeError, uninstall, queue, item_mode=mode)
            self.assertFalse(_valid_uninstall(queue))
        # END mode LOOP
