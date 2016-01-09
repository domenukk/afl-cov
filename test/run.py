#!/usr/bin/env python

from aflcov import *
import argparse
import sys, os
try:
    import subprocess32 as subprocess
except ImportError:
    import subprocess

def main():

    cargs = parse_cmdline()

    ### config
    tmp_file      = './tmp_cmd.out'
    test_cmd      = './test-afl-cov.py'

    ### the AFL test cases in the test suite are built against this
    ### commit in the fwknop code base
    fwknop_commit = 'e3ae6747'

    fwknop_codecov_dir     = 'fwknop-codecov.git'
    fwknop_codecov_compile = './compile/afl-compile-code-coverage.sh'

    fwknop_afl_dir     = 'fwknop-afl.git'
    fwknop_afl_compile = './compile/afl-compile.sh'

    ### system commands that we require
    cmds = {
        'git':'',
        'lcov':'',
        'make':'',
        'genhtml':'',
        'afl-fuzz':'',
        'python':'',
    }

    print "[+] Starting up afl-cov test suite..."

    ### make sure required system binaries are installed

    for cmd in cmds:
        cmds[cmd] = which(cmd)
        if not cmds[cmd]:
            print "[*] Could not find command '%s', exiting." % (cmd)
            return
    print "[+] Required binaries exist."

    ### clone the fwknop repository since the test suite operates
    ### against fwknop code
    if not is_dir(fwknop_codecov_dir):
        print "[+] (Code cov) cloning fwknop repo: %s" % (cargs.fwknop_git)
        do_cmd("%s clone %s %s" % (cmds['git'],
            cargs.fwknop_git, fwknop_codecov_dir), None)

    if not is_dir(fwknop_codecov_dir):
        print "[*] Could not clone %s, set a different --fwknop-git path?"
        return

    if not is_dir(fwknop_afl_dir):
        print "[+] (AFL support) Cloning fwknop repo: %s" % (cargs.fwknop_git)
        do_cmd("%s clone %s %s" % (cmds['git'],
            fwknop_codecov_dir, fwknop_afl_dir), None)

    ### build both fwknop repositories under the specified commit
    build_fwknop(fwknop_codecov_dir,
            fwknop_commit, fwknop_codecov_compile, cmds)
    build_fwknop(fwknop_afl_dir,
            fwknop_commit, fwknop_afl_compile, cmds)

    ### run the actual tests
    print "[+] Running afl-cov tests..."
    subprocess.call("%s %s" % (cmds['python'], test_cmd),
            stdin=None, shell=True)

    return

def build_fwknop(cdir, commit, compile_cmd, cmds):

    curr_dir = os.getcwd()
    os.chdir(cdir)
    if os.path.exists('./server/.libs/fwknopd'):
        do_cmd("%s clean" % (cmds['make']), None)
    do_cmd("%s checkout %s" % (cmds['git'], commit), None)
    do_cmd("./autogen.sh", None)

    print "[+] Compiling %s with test/afl/%s..." % (cdir, compile_cmd)
    os.chdir('./test/afl')
    do_cmd("%s" % (compile_cmd), None)
    os.chdir(curr_dir)

    return

def do_cmd(cmd, tmp_file):

    out = []

    fh = None
    if tmp_file:
        fh = open(tmp_file, 'w')
    else:
        fh = open(os.devnull, 'w')

    subprocess.call(cmd, stdin=None,
            stdout=fh, stderr=subprocess.STDOUT, shell=True)

    fh.close()

    if tmp_file:
        with open(tmp_file, 'r') as f:
            for line in f:
                out.append(line.rstrip('\n'))

    return out

def parse_cmdline():

    p = argparse.ArgumentParser()

    p.add_argument("--fwknop-git", type=str,
            help="Location of fwknop git repository",
            default="https://github.com/mrash/fwknop.git")

    return p.parse_args()

if __name__ == "__main__":
    sys.exit(main())
