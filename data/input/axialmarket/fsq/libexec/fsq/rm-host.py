#!/usr/bin/env python
# fsq-add-host(1) -- a program for uninstalling a fsq host queue.
#
# @author: Jeff Rand <jeff.rand@axial.net>
# @depends: fsq(1), fsq(7), python (>=2.7)
#
# This software is for POSIX compliant systems only.
import getopt
import sys
import fsq
import os

_PROG = "fsq-rm-host"
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
              os.path.basename(_PROG))
                                                      , f)
        shout('        host queue [queue [...]]', f)
    return 0 if asked_for else fsq.const('FSQ_FAIL_PERM')

# TODO add -f --force
def main(argv):
    global _PROG, _VERBOSE
    flag = None
    force = False

    _PROG = argv[0]
    try:
        opts, args = getopt.getopt(argv[1:], 'hvf', ( '--help',
                                   '--verbose', '--force', ))
        for flag, opt in opts:
            if flag in ( '-v', '--verbose', ):
                _VERBOSE = True
            if flag in ( '-f', '--force', ):
                force = True
            elif flag in ( '-h', '--help', ):
                return usage(1)

        if 2 > len(args):
            return usage()

        for queue in args[1:]:
            chirp('removing host {0} for queue {1}'.format(args[0], queue))
            try:
                fsq.uninstall_host(queue, args[0])
            except fsq.FSQInstallError:
                if force:
                    pass
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
