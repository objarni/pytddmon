import subprocess
import os

def run_pytddmon_in_test_mode(dir = None):
    subprocess.call(['python', '../pyTDDmon.pyw', '--log-and-exit'])
    gui_info = get_log_as_dictionary()
    os.unlink('pyTDDmon.log')
    return gui_info

def get_log_as_dictionary():
    f = open('pyTDDmon.log', 'r')
    rows = f.readlines()
    f.close()
    dict = {}
    for row in rows:
        (name, splitter, value) = row.partition('=')
        dict[name] = value.strip()
    return dict

