#!/usr/bin/env python
# fsq-add-host(1) -- a program for installing a fsq host queue.
#
# @author: Jeff Rand <jeff.rand@axial.net>
# @depends: fsq(1), fsq(7), python (>=2.7)
#
# This software is for POSIX compliant systems only.
import getopt
import sys
import fsq
import os
import errno

_PROG = "fsq-add-host"
_VERBOSE = False
_CHARSET = fsq.const('FSQ_CHARSET')

def chirp(msg):
    if _VERBOSE:
        shout(msg)

def shout(msg, f=sys.stderr):
    '''Log to file (usually stderr), with progname: <log>'''
    print >> f, "{0}: {1}".format(_PROG, msg)
    f.flush()

def usage(asked_for=0):
    '''Exit with a usage string, used for bad argument or with -h'''
    exit =  fsq.const('FSQ_SUCCESS') if asked_for else\
                fsq.const('FSQ_FAIL_PERM')
    f = sys.stdout if asked_for else sys.stderr
    shout('{0} [opts] host queue [queue [...]]'.format(
          os.path.basename(_PROG)), f)
    if asked_for:
        shout('{0} [-h|--help] [-v|--verbose] [-f|--force]'.format(
              os.path.basename(_PROG)), f)
        shout('        [-i|--ignore-exists]', f)
        shout('        [-o owner|--owner=user|uid]', f)
        shout('        [-g group|--group=group|gid]', f)
        shout('        [-m mode|--mode=int]', f)
        shout('        host queue [queue [...]]', f)
    return 0 if asked_for else fsq.const('FSQ_FAIL_PERM')

def main(argv):
    global _PROG, _VERBOSE
    force = False
    ignore = False
    flag = None

    _PROG = argv[0]
    try:
        opts, args = getopt.getopt(argv[1:], 'hvfo:g:m:i', ( '--help',
                                   '--force', '--verbose', '--owner',
                                   '--group', '--mode', '--ignore-exists', ))
        for flag, opt in opts:
            if flag in ( '-v', '--verbose', ):
                _VERBOSE = True
            elif flag in ( '-f', '--force', ):
                force = True
            elif flag in ( '-i', '--ignore-exists', ):
                ignore = True
            elif flag in ( '-o', '--owner', ):
                for c in ( 'FSQ_QUEUE_USER', 'FSQ_ITEM_USER', ):
                    fsq.set_const(c, opt)
            elif flag in ( '-g', '--group', ):
                for c in ( 'FSQ_QUEUE_GROUP', 'FSQ_ITEM_GROUP', ):
                    fsq.set_const(c, opt)
            elif flag in ( '-m', '--mode', ):
                for c in ( 'FSQ_QUEUE_MODE', 'FSQ_ITEM_MODE', ):
                    fsq.set_const(c, opt)
            elif flag in ( '-h', '--help', ):
                return usage(1)

        if 2 > len(args):
            return usage()

        host = args[0]

        for queue in args[1:]:
            try:
                chirp('installing host {0} to {1}'.format(host, queue))
                fsq.install_host(queue, host)
            except fsq.FSQInstallError, e:
                if e.errno == errno.ENOTEMPTY or e.errno == errno.ENOTDIR:
                    if force:
                        fsq.uninstall_host(queue, *host)
                        fsq.install_host(queue, *host)
                    elif ignore:
                        chirp('skipping {0}; already installed'.format(queue))
                    else:
                        raise
                else:
                    raise

    except ( fsq.FSQEnvError, fsq.FSQCoerceError, ):
        shout('invalid argument for flag: {0}'.format(flag))
        return fsq.const('FSQ_FAIL_PERM')
    except fsq.FSQInstallError, e:
        shout(e.strerror)
        return fsq.const('FSQ_FAIL_TMP')
    except getopt.GetoptError, e:
        shout('invalid flag: -{0}{1}'.format('-' if 1 < len(e.opt) else '',
              e.opt))
        return fsq.const('FSQ_FAIL_TMP')

if __name__ == '__main__':
    main(sys.argv)
