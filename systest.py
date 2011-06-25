import os
import subprocess

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

def compare_logs_in_dir(testdir):
    gotinfo = get_log(testdir, "pytddmon.log")
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
    rootdir = os.getcwd()
    pytddmon_path = os.path.join(rootdir, "pytddmon.pyw")
    names = os.listdir("systest")
    for name in names:
        path = os.path.join(rootdir, "systest", name)
        if os.path.isdir(path):
            os.chdir(path)
            cmdline = ['python', pytddmon_path, "--log-and-exit"]
            args = get_args(path)
            cmdline.extend(args)
            try:
                subprocess.check_call(cmdline, stdout=None, stderr=None)
            except:
                print(" .. in test: " + path + "\n")
            compare_logs_in_dir(path)


if __name__ == "__main__":
    run_all()
    