import subprocess

def run_pytddmon_in_test_mode():
    subprocess.call(['python', 'pyTDDmon.pyw', '--log-and-exit'])
    return get_log_as_dictionary()

def get_log_as_dictionary():
    f = open('pyTDDmon.log', 'r')
    rows = f.readlines()
    f.close()
    dict = {}
    for row in rows:
        (name, splitter, value) = row.partition('=')
        dict[name] = value.strip()
    return dict

