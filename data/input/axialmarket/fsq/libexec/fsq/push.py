#!/usr/bin/env python
# fsq-push(1) -- a program for pushing queue items to remote queues
#
# @author: Jeff Rand <jeff.rand@axial.net>
# @depends: fsq(1), fsq(7), python (>=2.7)
#
# This software is for POSIX compliant systems only.
import getopt
import sys
import fsq
import os

_PROG = "fsq-push"
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
    shout('{0} [opts] src_queue trg_queue host item_id [item_id [...]]'.format(
          os.path.basename(_PROG)), f)
    if asked_for:
        shout('{0} [-p|--protocol=jsonrpc] [-L|--no-lock] [-t|--trigger] '\
              '[-i|--ignore-listener] <proto>://<host>:<port>/url'\
              .format(os.path.basename(_PROG)), f)
        shout('{0} [-p|--protocol=jsonrpc] [-L|--no-lock] [-t|--trigger]'\
              '[-i|--ignore-listener] unix://var/sock/foo.sock'\
              .format(os.path.basename(_PROG)), f)
        shout('        src_queue trg_queue host_queue item [item [...]]', f)
    return exit

def main(argv):
    global _PROG, _VERBOSE
    protocol = 'jsonrpc'
    lock, trigger, ignore_listener = True, False, False

    _PROG = argv[0]
    try:
        opts, args = getopt.getopt(argv[1:], 'vhLtip:',
                     ( '--verbose', '--help', '--no-lock', '--trigger',
                       '--ignore-listener', '--protocol=', ))
        for flag, opt in opts:
            if flag in ( '-v', '--verbose', ):
                _VERBOSE = True
            if flag in ( '-p', '--protocol', ):
                protocol = opt
            if flag in ( '-L', '--no-lock', ):
                lock = False
            if flag in ( '-t', '--trigger', ):
                trigger = True
            if flag in ( '-i', '--ignore-listener', ):
                ignore_listener = True
            elif flag in ( '-h', '--help', ):
                return usage(1)

        if 5 > len(args):
            return usage()
        remote = args[0]
        src_queue = args[1]
        trg_queue = args[2]
        host = args[3]

        for item_id in args[4:]:
            chirp('pushing item {0} to remote {1} from queue {2}, host queue '\
                  '{3} to queue {4}'.format(item_id, remote, src_queue, host,
                                            trg_queue))
            item = fsq.FSQWorkItem(src_queue, item_id , host=host, lock=lock)
            fsq.push(item, remote, trg_queue, protocol=protocol)
            if trigger:
                fsq.remote_trigger_pull(remote, trg_queue,
                                   ignore_listener=ignore_listener,
                                   protocol=protocol)

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
