#! /usr/bin/env python
#coding: utf-8
import os
import shutil
import subprocess
from optparse import OptionParser

def get_log_as_dictionary(path):
    f = open(path, 'r')
    rows = f.readlines()
    f.close()
    dict = {}
    for row in rows:
        (name, splitter, value) = row.partition('=')
        dict[name] = value.strip()
    return dict

def get_log(testdir, logname):
    fullpath = os.path.join(testdir, logname)
    return get_log_as_dictionary(fullpath)

def pretty_please(testdir):
    testdir = testdir.replace('\\', '/')
    testdir = testdir.split('/')[-1]
    testdir = testdir.replace('_', ' ')
    testdir = testdir.title()
    return testdir

def compare(testdir, what, gotdict, expdict):
    got = gotdict[what]
    exp = expdict[what]
    pretty = pretty_please(testdir)
    if got != exp:
        print(pretty + ": expected " + exp + " " + what + " test(s), got " + got)

def compare_logs(testdir, got, exp):
    compare(testdir, 'green', got, exp)
    compare(testdir, 'total', got, exp)

def compare_logs_in_dir(testdir, outputdir):
    gotinfo = get_log(outputdir, "pytddmon.log")
    expinfo = get_log(testdir, "expected.log")
    compare_logs(testdir, gotinfo, expinfo)

def get_args(path):
    argspath = os.path.join(path, "args.txt")
    if not os.path.exists(argspath):
        return []
    f = open(argspath, "r")
    content = f.read().strip()
    f.close()
    return content.split()

def run_all():
    (tmpdir, cleanup) = parse_commandline()
    cwd = os.getcwd()
    pytddmon_path = os.path.join(cwd, "../src/pytddmon.py")
    names = os.listdir(cwd)
    for name in names:
        path = os.path.join(cwd, name)
        if os.path.isdir(path):
            os.chdir(path)
            cmdline = ['python', pytddmon_path, "--log-and-exit"]
            log_path = path
            if tmpdir:
                log_path = os.path.join(tmpdir, name)
                log_name = os.path.join(log_path, 'pytddmon.log')
                if not os.path.exists(log_path):
                    os.mkdir(log_path)
                    touch(log_name)
                cmdline.extend(['--log-path', log_name])
            args = get_args(path)
            cmdline.extend(args)
            try:
                subprocess.check_call(cmdline, stdout=None, stderr=None)
            except:
                print(" .. in test: " + path + "\n")
            compare_logs_in_dir(path, log_path)
            if tmpdir and cleanup:
                shutil.rmtree(log_path)

    os.chdir(cwd)

def touch(fname, times=None):
    with open(fname, 'a'):
        os.utime(fname, times)

def parse_commandline():
    parser = OptionParser()
    parser.add_option('-t', '--tmpdir', help='Write log files to TMPDIR')
    parser.add_option('-c',
                      '--clean-up',
                      action='store_true',
                      default=False,
                      help='If TMPDIR is defined, then clean up the temporary files and directories created')

    (options, args) = parser.parse_args()
    return options.tmpdir, options.clean_up

if __name__ == "__main__":
    run_all()
