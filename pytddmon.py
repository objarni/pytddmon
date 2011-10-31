#! /usr/bin/env python
#coding: utf-8

'''
Copyright (c) 2009,2010,2011 Olof Bjarnason

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

CONTRIBUTIONS
Fredrik Wendt: 
    Help with Tkinter implementation (replacing the pygame dependency).
KrunoSaho: 
    Added always-on-top to the pytddmon window.
Neppord(Samuel Ytterbrink): 
    Print(".") will not screw up test-counting (it did before).
    Docstring support.
    Recursive discovery of tests.
    Refactoring to increase Pylint score from 6 to 9.5 out of 10 (!).
Rafael Capucho:
    Python shebang at start of script, enabling "./pytddmon.py" on unix systems
'''

import os
import sys
import tempfile
import atexit
import shlex
import platform
import optparse
import re

from time import gmtime, strftime
from subprocess import Popen, PIPE, STDOUT

ON_PYTHON3 = sys.version_info[0] == 3
ON_WINDOWS = platform.system() == "Windows"

if not ON_PYTHON3:
    import Tkinter as tk
else:
    import tkinter as tk

# Constants

TEMP_FILE_DIR_NAME = tempfile.mkdtemp()
RUN_TESTS_SCRIPT_FILE = os.path.join(TEMP_FILE_DIR_NAME, 'pytddmon_tmp.py')
TEMP_OUT_FILE_NAME = os.path.join(TEMP_FILE_DIR_NAME, "out")
# If pytddmon is run in test mode, it will:
# 1. display the GUI for a very short time
# 2. write a log file, containing the information displayed 
#    (most notably green/total)
# 3. exit
TEST_MODE_LOG_FILE = 'pytddmon.log'
TEST_FILE_REGEXP = "test_.*\\.py"
PYTHON_FILE_REGEXP = ".*\\.py"

# End of Constants

####
## Core
####

class Pytddmon(object):
    """The core class, all functionality are agregated and lives inside this 
    class."""
    def __init__(self, project_name="<pytddmon>", file_strategies=None, test_strategies=None):
        self.project_name = project_name
        # The different ways pytddmon can find changes to a project
        self.file_strategies = (
            file_strategies if file_strategies != None else []
        )
        # The different ways pytddmon can find tests and run them
        self.test_strategies = (
            test_strategies if test_strategies != None else []
        )
        self.total_tests_run = 0
        self.total_tests_passed = 0
        self.last_testrun_time = -1
        self.test_loggs = []
        self.changed_files = []

    def which_files_has_changed(self):
        """Returns list of changed files."""
        self.changed_files = []
        for file_strategy in self.file_strategies:
            self.changed_files.extend(file_strategy.which_files_has_changed())
        return self.changed_files

    def run_tests(self, file_paths=None):
        """Runns all tests and updates the time it took and the total test run
        and passed."""
        import time
        file_paths = file_paths if file_paths != None else []
        start = time.time()
        self.total_tests_run = 0
        self.total_tests_passed = 0
        self.test_loggs = []
        for test_strategy in self.test_strategies:
            tests_run, passed, log = test_strategy.run_tests(file_paths)
            self.total_tests_run += tests_run
            self.total_tests_passed += passed
            self.test_loggs.append(log)
        self.last_testrun_time = time.time() - start

    def main(self):
        """This is the main loop body"""
        file_paths = self.which_files_has_changed()
        if file_paths != []:
            self.run_tests(file_paths)

    def get_loggs(self):
        """Creates a readabel log of the all test strategies run""" 
        return "===Log delemeter===\n".join(self.test_loggs)

####
## Hashing
####

class DefaultHasher(object):
    """A simple hasher which takes the size and the modified time and returns
    a checksum."""
    def __init__(self, os_module):
        self.os_module = os_module
    def __call__(self, file_path):
        """Se Class description."""
        stat = self.os_module.stat(file_path)
        return stat.st_size + (stat.st_mtime * 1j)
####
## File Strategies
####

class StaticFileStartegy(object):
    """Looks for changeds in a static set of files."""
    def __init__(self, file_paths, hasher=DefaultHasher(os)):
        self.file_paths = None
        self.last_hash = None
        self.change_file_set(file_paths)
        self.hasher = hasher

    def change_file_set(self, file_paths):
        self.file_paths = set([
            os.path.abspath(file_path) for file_path in file_paths
        ])
        self.last_hash = [-1] * len(self.file_paths)

    def which_files_has_changed(self):
        """Looks through all file paths and return which of them has changed."""
        file_paths_to_return = []
        hashes = self.hash_files()
        iteration = zip(self.last_hash, hashes, self.file_paths)
        for old_hash, new_hash, file_path in iteration:
            if old_hash != new_hash:
                file_paths_to_return.append(file_path)
        self.last_hash = hashes
        return file_paths_to_return

    def hash_files(self):
        """Helper method to hash all files."""
        return [
            self.hasher(file_path)
            for file_path in self.file_paths
        ]

class RecursiveRegexpFileStartegy(object):
    """Looks for files recursivly from a root dir with a specific regexp
    pattern."""
    def __init__(self, root, expr, walker=os.walk, hasher=DefaultHasher(os)):
        self.walker = walker
        self.hasher = hasher
        self.root = os.path.abspath(root)
        self.expr = expr
        self.pares = []

    def get_pares(self):
        """calculates the new list of pares (path, hash)"""
        file_paths = set()
        for path, _folder, filenames in self.walker(self.root):
            for filename in filenames:
                if re_complete_match(self.expr, filename):
                    file_paths.add(
                        os.path.abspath(os.path.join(path, filename))
                    )
        return [(file_path, self.hasher(file_path)) for file_path in file_paths]

    def which_files_has_changed(self):
        """Looks for files recursivly from a root dir with a specific regexp"""
        paths = []
        new_pares = self.get_pares()
        new_pares.sort()
        new = iter(new_pares)
        old = iter(self.pares)
        try:
            new_path, new_hash = new.next()
            old_path, old_hash = old.next()
            while True:
                if new_path == old_path and new_hash == old_hash:
                    new_path, new_hash = new.next()
                    old_path, old_hash = old.next()
                elif new_path != old_path:
                    if new_path < old_path:
                        paths.append(new_path)
                        new_path, new_hash = new.next()
                    else:
                        paths.append(old_path)
                        old_path, old_hash = old.next()
                else:
                    paths.append(new_path)
                    new_path, new_hash = new.next()
                    old_path, old_hash = old.next()
        except StopIteration:
            paths += (
                [path for path, _hash in new] +
                [path for path, _hash in old]
            )
        self.pares = new_pares
        return paths

class RecursiveGlobFileStartegy(RecursiveRegexpFileStartegy):
    def __init__(self, root, expr, walker=os.walk, hasher=DefaultHasher(os)):
        import fnmatch
        super(RecursiveGlobFileStartegy, self).__init__(
            root=root,
            expr=fnmatch.translate(expr),
            walker=walker,
            hasher=hasher
        )

####
## Test Strategies
####

def log_exceptions(func):
    from functools import wraps
    @wraps(func)
    def wraper(*a,**k):
        try:
            return func(*a, **k)
        except:
            import traceback
            return (0, 1j, traceback.format_exc())
    return wraper


@log_exceptions
def run_unittests(arguments):
    """Loads all unittests in file, with root as package location."""
    root, file_path = arguments
    import unittest
    import StringIO
    module = file_name_to_module(root, file_path)
    err_log = StringIO.StringIO()
    test_loader = unittest.TestLoader()
    suite = test_loader.loadTestsFromName(module)
    text_test_runner = unittest.TextTestRunner(stream=err_log)
    result = text_test_runner.run(suite)
    return (
        result.testsRun - len(result.failures),
        result.testsRun, 
        err_log.getvalue()
    )
@log_exceptions
def run_doctests(arguments):
    """Loads all doctests in file, with root as package location."""
    root, file_path = arguments
    import unittest
    import doctest
    import StringIO
    module = file_name_to_module(root, file_path)
    err_log = StringIO.StringIO()
    try:
        suite = doctest.DocTestSuite(module, optionflags=doctest.ELLIPSIS)
    except ValueError:
        return (
        0,
        0,
        """Error when trying to find doctests in:
            module:%r
            path:%r""" % (module. file_path)
        )
    text_test_runner = unittest.TextTestRunner(stream=err_log)
    result = text_test_runner.run(suite)
    return (result.testsRun - len(result.failures), result.testsRun, err_log.getvalue())


    

class StaticUnitTestStrategy(StaticFileStartegy):
    """Runns a Static set of files as if thay where Unitttest suits. They must
    however be on the python path or be inside a package that is."""
    def run_tests(self, file_paths):
        """Runns all staticly selected files as if they where UnitTests"""
        from multiprocessing import Pool
        file_paths_to_run = []
        for file_path in self.file_paths:
            file_paths_to_run.append((os.getcwd(), file_path))
        pool = Pool()
        results = pool.map(run_unittests, file_paths_to_run)
        loggs = []
        all_green = 0
        all_total = 0
        for (green, total, log), (_rt, pth) in zip(results, file_paths_to_run):
            all_green += green
            all_total += total
            loggs.append("file:%s\n%s" % (pth, log))
            
        return (all_green, all_total, "\n".join(loggs))

class StaticDoctestStrategy(StaticFileStartegy):
    """Runns a Static set of files as if thay where Doctests, using unittests
    whraper. They must however be on the python path or be inside a package
    that is."""
    def run_tests(self, file_paths):
        """Runns all staticly selected files as if they where doctest"""
        from multiprocessing import Pool
        file_paths_to_run = []
        for file_path in self.file_paths:
            file_paths_to_run.append(os.getcwd(), file_path)
        pool = Pool()
        results = pool.map(run_doctests, file_paths_to_run)
        loggs = []
        all_green = 0
        all_total = 0
        for (green, total, log), (_rt, pth) in zip(results, file_paths_to_run):
            all_green += green
            all_total += total
            loggs.append("file:%s\n%s" % (pth, log))
            
        return (all_green, all_total, "\n".join(loggs))

class RecursiveRegexpTestStartegy(object):
    """Recursivly looking for tests in packages with a filename matching the 
    regexpr."""
    def __init__(self, root, expr, walker=os.walk):
        self.root = os.path.abspath(root)
        self.expr = expr
        self.walker = walker

    @staticmethod
    def is_package(path, folder):
        """Check if folder in path is a package"""
        return os.path.isfile(os.path.join(path,folder,"__init__.py"))

    def run_tests(self, file_paths):
        from multiprocessing import Pool
        file_paths_to_run = [] 
        for path, folders, file_paths in self.walker(self.root):
            to_remove = []
            for folder in folders:
                if not self.is_package(path, folder):
                    to_remove.append(folder)
            for folder in to_remove:
                folders.remove(folder)
            for file_path in file_paths:
                if re_complete_match(self.expr, file_path):
                    file_paths_to_run.append(
                        (
                            self.root,
                            os.path.abspath(
                                os.path.join(
                                    path,
                                    file_path
                                )
                            )
                        )
                    
                    )
        pool = Pool()
        results = pool.map(
            run_unittests,
            file_paths_to_run
        )
        all_green = 0
        all_total = 0
        loggs = []
        for (green, total, log), (_rt, pth) in zip(results, file_paths_to_run):
            all_green += green
            all_total += total
            loggs.append("file:%s\n%s" % (pth, log))
        return (all_green, all_total, "\n".join(loggs))
####
## GUI
####

def build_tk_gui(pytddmon):
    if not ON_PYTHON3:
        import Tkinter as tk
    else:
        import tkinter as tk
    root = tk.Tk()
    root.wm_attributes("-topmost", 1)
    if ON_WINDOWS:
        root.attributes("-toolwindow", 1)
        print("Minimize me!")
    frame = tk.Frame(root)
    frame.master.title("pytddmon")  # Sets the title of the gui
    frame.master.resizable(False, False)    # Forces the window to not be resizeable
    button = tk.Label(
        frame,
        text = "loading...",
        relief='raised',
        font=("Helvetica", 28),
        justify=tk.CENTER,
        anchor=tk.CENTER
    )
    button.bind(
        "<Button-1>",
        lambda *a:message_window("monitoring: %s\ntime:%r\n%s" % (
            pytddmon.project_name,
            pytddmon.last_testrun_time, 
            pytddmon.get_loggs()
            ))
    )
    button.pack(expand=1, fill="both")
    color_picker = ColorPicker()
    def update_gui():
        color_picker.set_result(
            pytddmon.total_tests_passed,
            pytddmon.total_tests_run,
        )
        light, color = color_picker.pick()
        rgb = color_picker.translate_colure(light, color)
        color_picker.pulse()
        button.configure(
            bg=rgb,
            activebackground=rgb,
            text="%r/%r" % (
                pytddmon.total_tests_passed,
                pytddmon.total_tests_run
            )
        )
        frame.configure(background=rgb)
        #frame.grid()

        
    frame.grid()
    loop = lambda:pytddmon.main() or update_gui() or frame.after(750,loop)
    loop()
    root.mainloop()

####
## Un Organized
####

def re_complete_match(regexp, string_to_match):
    """Helper function that does a regexp check if the full string_to_match
    matches the regexp"""
    return bool(re.match(regexp+"$", string_to_match))

def file_name_to_module(base_path, file_name):
    r"""Converts filenames of files in packages to import friendly dot separated
    paths.

    Examples:
    >>> print(file_name_to_module("","pytddmon.pyw"))
    pytddmon
    >>> print(file_name_to_module("","pytddmon.py"))
    pytddmon
    >>> print(file_name_to_module("","tests/pytddmon.py"))
    tests.pytddmon
    >>> print(file_name_to_module("","./tests/pytddmon.py"))
    tests.pytddmon
    >>> print(file_name_to_module("",".\\tests\\pytddmon.py"))
    tests.pytddmon
    >>> print(file_name_to_module("/User/pytddmon\\ geek/pytddmon/","/User/pytddmon\\ geek/pytddmon/tests/pytddmon.py"))
    tests.pytddmon
    """
    symbol_stripped = os.path.relpath(file_name, base_path)
    for symbol in r"/\.":
        symbol_stripped = symbol_stripped.replace(symbol, " ")
    words = symbol_stripped.split()
    module_words = words[:-1] # remove .py/.pyw
    module_name = '.'.join(module_words)
    return module_name

class ColorPicker:
    """
    ColorPicker decides the background color the pytddmon window,
    based on the number of green tests, and the total number of
    tests. Also, there is a "pulse" (light color, dark color),
    to increase the feeling of continous testing.
    """
    color_table = {
        (True, 'green'): '0f0',
        (False, 'green'): '0c0',
        (True, 'red'): 'f00',
        (False, 'red'): 'c00',
        (True, 'orange'): 'fc0',
        (False, 'orange'): 'ca0',
        (True, 'gray'): '999',
        (False, 'gray'): '555'
    }

    def __init__(self):
        self.color = 'green'
        self.light = True

    def pick(self):
        "returns the tuple (light, color) with the types(bool ,str)"
        return (self.light, self.color)

    def pulse(self):
        "updates the light state"
        self.light = not self.light

    def reset_pulse(self):
        "resets the light state"
        self.light = True

    def set_result(self, green, total):
        "calculates what color should be used and may reset the lightness"
        old_color = self.color
        self.color = 'green'
        if green.imag or total.imag:
            self.color = "orange"
        elif green == total-1:
            self.color = 'red'
        elif green < total-1:
            self.color = 'gray'
        if self.color != old_color:
            self.reset_pulse()
    @classmethod
    def translate_colure(cls, light, color):
        return "#" + cls.color_table[(light, color)]

def message_window(message):
    "creates and shows a window with the message"
    win = tk.Toplevel()
    win.wm_attributes("-topmost", 1)
    if ON_WINDOWS:
        win.attributes("-toolwindow", 1)
    win.title('Details')
    message = message.replace('\r\n', '\n')
    text = tk.Text(win)
    text.insert(tk.INSERT, message)
    text['state'] = tk.DISABLED
    text.pack(expand=1, fill='both')
    text.focus_set()


def parse_commandline():
    """
    returns (files, test_mode) created from the command line arguments
    passed to pytddmon.
    """
    parser = optparse.OptionParser()
    parser.add_option("--log-and-exit", action="store_true", default=False)
    (options, args) = parser.parse_args()
    return (args, options.log_and_exit)

def run():
    """
    The main function: basic initialization and program start
    """
    # Command line argument handling
    (static_file_set, test_mode) = parse_commandline()
    static_file_set = filter_existing_files(static_file_set)
    
    # Basic tkinter initialization
    root = tk.Tk()
    root.wm_attributes("-topmost", 1)
    if ON_WINDOWS:
        root.attributes("-toolwindow", 1)
        if not test_mode:
            print("Minimize me!")
       
    # Create main window
    if len(static_file_set)>0:
        PytddmonFrame(root, static_file_set, test_mode=test_mode)
    else:
        PytddmonFrame(root, test_mode=test_mode)

    # Main loop
    try:
        root.mainloop()
    except Exception as exception:
        print(exception)

if __name__ == '__main__':
    #run()
    pytddmon = Pytddmon(
        file_strategies=[
            RecursiveGlobFileStartegy(
                root=".",
                expr="*.py"
            )
        ],
        test_strategies=[
            RecursiveRegexpTestStartegy(
                root=".",
                expr="test_.*\\.py"
            )
        ]
    )
    build_tk_gui(pytddmon)

