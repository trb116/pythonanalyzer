#!/usr/bin/env python
# fsq-down(1) -- a program for turning off queues
#
# @author: O'Meara <will.omeara@axial.net>
#          Matthew Story <matt.story@axial.net>
# @depends: fsq(1), fsq(7), python (>=2.7)
#
# This software is for POSIX compliant systems only.
import getopt
import sys
import fsq
import os


_PROG = "fsq-down"
_VERBOSE = False
_CHARSET = fsq.const('FSQ_CHARSET')


def chirp(msg):
    if _VERBOSE:
        shout(msg)


def shout(msg, f=sys.stderr):
    '''Log to file (usually stderr), with progname: <log>'''
    print >> f, "{0}: {1}".format(_PROG, msg)
    f.flush()


def barf(msg, exit=None, f=sys.stderr):
    '''Exit with a log message (usually a fatal error)'''
    exit = fsq.const('FSQ_FAIL_TMP') if exit is None else exit
    shout(msg, f)
    sys.exit(exit)


def usage(asked_for=0):
    '''Exit with a usage string, used for bad argument or with -h'''
    exit =  fsq.const('FSQ_SUCCESS') if asked_for else\
                fsq.const('FSQ_FAIL_PERM')
    f = sys.stdout if asked_for else sys.stderr
    shout('{0} [opts] queue prog [args [...]]'.format(
          os.path.basename(_PROG)), f)
    if asked_for:
        shout('{0} [-h|--help] [-v|--verbose]'.format(
            os.path.basename(_PROG)), f)
        shout('        [-u user|--user=user]', f)
        shout('        [-g group|--group=group]', f)
        shout('        [-m mode|--mode=mode]', f)
        shout('        queue [queue [...]]', f)
    sys.exit(exit)


# all fsq commands use a main function
def main(argv):
    global _PROG, _VERBOSE

    _PROG = argv[0]
    try:
        opts, args = getopt.getopt(
            argv[1:], 
            'hvu:g:m:', ( 
                'help', 
                'verbose',
                'user=',
                'group=',
                'mode=', ))
    except getopt.GetoptError, e:
        barf('invalid flag: -{0}{1}'.format('-' if 1 < len(e.opt) else '',
             e.opt))
    try:
        user, group, mode = None, None, None
        for flag, opt in opts:
            if '-v' == flag or '--verbose' == flag:
                _VERBOSE = True
            elif '-u' == flag or '--user' == flag:
                user = opt
            elif '-g' == flag or '--group' == flag:
                group = opt
            elif '-m' == flag or '--mode' == flag:
                try:
                    mode = int(opt, 8)
                except ValueError:
                    barf('invalid mode: {}'.format(opt))
            elif '-h' == flag or '--help' == flag:
                usage(1)
    except ( fsq.FSQEnvError, fsq.FSQCoerceError, ):
        barf('invalid argument for flag: {0}'.format(flag))

    try:
        for arg in args:
            fsq.down(queue=arg, user=user, group=group, mode=mode)
            chirp('{0}: down'.format(arg)) 
    except fsq.FSQCoerceError, e:
        barf('cannot coerce queue; charset={0}'.format(_CHARSET))
    except fsq.FSQError, e:
        shout(e.strerror.encode(_CHARSET))


if __name__ == '__main__':
    main(sys.argv)

