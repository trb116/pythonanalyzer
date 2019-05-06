#!/usr/bin/env python
# fsq-scan(1) -- a program for scanning a fsq queue, and executing programs
#                with item arguments and environments. See fsq.utility for more
#                information.
#
# @author: Matthew Story <matt.story@axial.net>
# @depends: fsq(1), fsq(7), python (>=2.7)
#
# TODO: Concurrency? -- not right now
#
# This software is for POSIX compliant systems only.
import getopt
import sys
import fsq
import os

_PROG = "fsq-scan"
_VERBOSE = False

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
        shout('{0} [-h|--help] [-v|--verbose] [-e|--env]'\
              ' [-E|--no-env]'.format(os.path.basename(_PROG)), f)
        shout('        [-n|--no-open] [-i|--ignore-down]', f)
        shout('        [-k|--empty-ok] [-D|--no-done]', f)
        shout('        [-l|--lock] [-L|--no-lock]', f)
        shout('        [-t ttl_seconds|--ttl=seconds]', f)
        shout('        [-m max_tries|--max-tries=int]', f)
        shout('        [-a all_hosts |--all-hosts]', f)
        shout('        [-A host |--host=host]', f)
        shout('        [-S success_code|--success-code=int]', f)
        shout('        [-T fail_tmp_code|--fail-tmp-code=int]', f)
        shout('        [-F fail_perm_code|--fail-perm-code=int]', f)
        shout('        [-r rate | --max-rate=int]', f)
        shout('        queue prog [args [...]]', f)
    sys.exit(exit)

# all fsq commands use a main function
def main(argv):
    global _PROG, _VERBOSE
    # defaults
    set_env = True
    no_open = False
    ignore_down = False
    empty_ok = False
    no_done = False
    host = False
    hosts = []
    max_rate = None

    _PROG = argv[0]
    try:
        opts, args = getopt.getopt(argv[1:], 'hveEnilLkDt:m:S:T:F:aA:r:', ( 'help',
                                   'env', 'no-env', 'no-open', 'ignore-down',
                                   'lock', 'no-lock', 'empty-ok', 'no-done',
                                   'ttl=', 'max-tries=', 'success-code=',
                                   'fail-tmp-code=', 'fail-perm-code=',
                                   'verbose', 'all-hosts', 'host=', 'max-rate='))
    except getopt.GetoptError, e:
        barf('invalid flag: -{0}{1}'.format('-' if 1 < len(e.opt) else '',
             e.opt))
    try:
        for flag, opt in opts:
            if '-v' == flag or '--verbose' == flag:
                _VERBOSE = True
            elif '-e' == flag or '--env' == flag:
                set_env = True
            elif '-E' == flag or '--no-env' == flag:
                set_env = False
            elif '-n' == flag or '--no-open' == flag:
                no_open = True
            elif '-i' == flag or '--ignore-down' == flag:
                ignore_down = True
            elif '-l' == flag or '--lock' == flag:
                fsq.set_const('FSQ_LOCK', True)
            elif '-L' == flag or '--no-lock' == flag:
                fsq.set_const('FSQ_LOCK', False)
            elif '-k' == flag or '--empty-ok' == flag:
                empty_ok = True
            elif '-D' == flag or '--no-done' == flag:
                no_done = True
            elif '-a' == flag or '--all-hosts' == flag:
                host = True
            elif '-A' == flag or '--hosts' == flag:
                hosts.append(opt)
                host = True
            elif '-t' == flag or '--ttl' == flag:
                fsq.set_const('FSQ_TTL', opt)
            elif '-m' == flag or '--max-tries' == flag:
                fsq.set_const('FSQ_MAX_TRIES', opt)
            elif '-S' == flag or '--success-code' == flag:
                fsq.set_const('FSQ_SUCCESS', opt)
            elif '-T' == flag or '--fail-tmp-code' == flag:
                fsq.set_const('FSQ_FAIL_TMP', opt)
            elif '-F' == flag or '--fail-perm-code' == flag:
                fsq.set_const('FSQ_FAIL_PERM', opt)
            elif '-r' == flag or '--max-rate' == flag:
                try:
                    max_rate = int(opt)
                except ValueError:
                    raise fsq.FSQCoerceError
            elif '-h' == flag or '--help' == flag:
                usage(1)
    except ( fsq.FSQEnvError, fsq.FSQCoerceError, ):
        barf('invalid argument for flag: {0}'.format(flag))

    # validate args
    num_required = 1 if empty_ok else 2
    if num_required > len(args):
        usage()
    exec_args = tuple(args[1:])
    fsq.fork_exec_items(args[0], ignore_down=ignore_down, host=host,
                        no_open=no_open, hosts=hosts if hosts else None,
                        no_done=no_done, set_env=set_env, exec_args=exec_args,
                        verbose=_VERBOSE, empty_ok=empty_ok, max_rate=max_rate)

if __name__ == '__main__':
    main(sys.argv)
