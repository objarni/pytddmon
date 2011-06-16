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
    #print("Comparing logs in " + testdir)
    gotinfo = get_log(testdir, "pyTDDmon.log")
    expinfo = get_log(testdir, "expected.log")
    compare_logs(testdir, gotinfo, expinfo)

def run_all():
    systestdir = os.getcwd()
    names = os.listdir(".")
    for name in names:
        if os.path.isdir(name):
            testdir = os.path.join(systestdir, name)
            os.chdir(testdir)
            subprocess.call(['python', "../../pyTDDmon.pyw", "--log-and-exit"])
            compare_logs_in_dir(testdir)
            os.chdir(systestdir)


if __name__ == "__main__":
    run_all()
    