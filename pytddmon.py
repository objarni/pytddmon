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
    def __init__(self, file_strategies=None, test_strategies=None):
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
        self.last_testrun_time = 0
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
            paths += [path for path in new] + [path for path in old]
        self.pares = new_pares
        return paths

class RecursiveGlobFileStartegy(RecursiveRegexpFileStartegy):
    def __init__(self, root, expr, walker=os.walk, hasher=DefaultHasher(os)):
        import fnmatch
        super(RecursiveGlobFileStartegy, self).__init__(
            root,
            fnmatch.translate(expr),
            walker=walker,
            hasher=hasher
        )

####
## Test Strategies
####

class StaticUnitTestStrategy(StaticFileStartegy):
    """Runns a Static set of files as if thay where Unitttest suits. They must
    however be on the python path or be inside a package that is."""
    def run_tests(self, file_paths):
        """Runns all staticly selected files as if they where UnitTests"""
        from multiprocessing import Pool
        file_paths_to_run = []
        for file_path in self.file_paths:
            file_paths_to_run.append(file_path)
        pool = Pool()
        results = pool.map(self.run_tests, file_paths_to_run)
        loggs = []
        all_green = 0
        all_total = 0
        for green, total, log in results:
            all_green += green
            all_total += total
            logg.append(log)
            
        return (all_green, all_total, "\n".join(loggs))

    @staticmethod
    def run_test(file_path):
        """Runns all unittests in file file_path. This should not be called
        without creating a new processs, due to that it will not reload modules
        ."""
        import unittest
        import StringIO
        module = file_name_to_module("", file_path)
        err_log = StringIO.StringIO()
        test_loader = unittest.TestLoader()
        suite = test_loader.loadTestsFromName(module)
        text_test_runner = unittest.TextTestRunner(stream=err_log)
        result = text_test_runner.run(suite)
        return (result.testsRun - len(result.failures), result.testsRun, err_log.getvalue())

class StaticDoctestStrategy(StaticFileStartegy):
    """Runns a Static set of files as if thay where Doctests, using unittests
    whraper. They must however be on the python path or be inside a package
    that is."""
    def run_tests(self, file_paths):
        """Runns all staticly selected files as if they where doctest"""
        from multiprocessing import Pool
        file_paths_to_run = []
        for file_path in self.file_paths:
            file_paths_to_run.append(file_path)
        pool = Pool()
        results = pool.map(self.run_tests, file_paths_to_run)
        loggs = []
        all_green = 0
        all_total = 0
        for green, total, log in results:
            all_green += green
            all_total += total
            logg.append(log)
            
        return (all_green, all_total, "\n".join(loggs))

    @staticmethod
    def run_test(file_path):
        """Runns all unittests in file file_path. This should not be called
        without creating a new processs, due to that it will not reload modules
        ."""
        import unittest
        import doctest
        import StringIO
        module = file_name_to_module("", file_path)
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

def RecursiveRegexpTestStartegy(object):
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
                    files_paths_to_run.append(
                        os.path.abspath(
                            os.path.join(
                                path,
                                file_path
                            )
                        )
                    
                    )
            pool = Pool()
            results = pool.map(self.run_tests, file_paths_to_run)
            all_green = 0
            all_total = 0
            loggs = []
            for green, total, log in results:
                all_green += green
                all_total += total
                loggs.append(log)
            return (all_green, all_total, "\n".join(loggs))
        
        def run_tests(self, file_path):
            """runs a test relative to root, this method needs to be called
            from a nother process cause it dont reload modules."""
            import unittest
            import StringIO
            module = file_name_to_module(self.root, file_path)
            err_log = StringIO.StringIO()
            test_loader = unittest.TestLoader()
            suite = test_loader.loadTestsFromName(module)
            text_test_runner = unittest.TextTestRunner(stream=err_log)
            result = text_test_runner.run(suite)
            return (result.testsRun - len(result.failures), result.testsRun, err_log.getvalue())
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
    button = tk.Lable(
        frame,
        text = "loading...",
        relief='raised',
        font=("Helvetica", 16),
        justify=tk.CENTER,
        anchor=tk.CENTER
    )
    button.bind(
        "<Button-1>",
        lambda:message_window("monitoring: %s\ntime:%d\n%s" % (
            pytddmon.project_name,
            pytddmon.last_testrun_time, 
            pytddmon.get_loggs()
            ))
    )
    self.button.pack(expand=1, fill="both")
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
            text=win_text(
                pytddmon.total_tests_passed,
                pytddmon.total_tests_run
            )
        )
        frame.configure(background=rgb)

        
    loop = lambda:pytddmon.main() or update_gui() or frame.after(750,loop)
    loop()

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

def build_run_script(files):
    """Compiles a script to run all tests in the files.

    >>> print(build_run_script(["pytddmon.py"]))
    import sys
    import unittest
    import doctest
    ...
    import pytddmon
    suite.addTests(load_module_tests(pytddmon))
    try:
        suite.addTests(doctest.DocTestSuite(pytddmon, optionflags=doctest.ELLIPSIS))
    except:pass
    ...
    """

    content = []
    content.append("import sys")
    content.append("import unittest")
    content.append("import doctest")
    content.append("")
    content.append("sys.path[0] = %r" % os.getcwd())
    content.append("suite = unittest.TestSuite()")
    content.append(
        "load_module_tests = unittest.defaultTestLoader.loadTestsFromModule"
        )
    content.append("")

    for filename in files:
        module = file_name_to_module("", filename)
        content.append('import ' + module)
        content.append('suite.addTests(load_module_tests(' + module + '))')
        content.append('try:')
        content.append(
            '    suite.addTests(doctest.DocTestSuite(' + 
            module + 
            ', optionflags=doctest.ELLIPSIS))'
            )
        content.append('except:pass')
        content.append('')
    
    content.append("if __name__ == '__main__':")
    content.append("    out = open(%r, 'w')" % TEMP_OUT_FILE_NAME)
    content.append("    unittest.TextTestRunner(stream=out).run(suite)")

    return "\n".join(content)

def calculate_checksum(filelist, fileinfo):
    """Generates a checksum for all the files in the file list."""
    val = 0
    for filename in filelist:
        val += (
            fileinfo.get_modified_time(filename) +
            (fileinfo.get_size(filename) * 1j) +
            fileinfo.get_name_hash(filename)
            )
    return val

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
        if green == total-1:
            self.color = 'red'
        if green < total-1:
            self.color = 'gray'
        if self.color != old_color:
            self.reset_pulse()
    @classmethod
    def translate_colure(cls, light, color):
        return "#" + cls.color_table[(light, color)]

def win_text(total_tests, passing_tests=0):
    """
    The text shown in the main window.
    """
    return "%d/%d" % (passing_tests, total_tests)

class ScriptWriter:
    """
    ScriptWriter: gets it's modules from the Finder, and
    writes a test script using the file writer and script
    builder.
    """
    def __init__(self, finder, file_writer, script_builder):
        self.finder = finder
        self.file_writer = file_writer
        self.script_builder = script_builder

    def write_script(self):
        """
        Finds the tests and Compiles the test runner script and writes it 
        to file. This is done with the help from the finder script builder and
        file writer.
        """
        modules = self.finder()
        result = self.script_builder(modules)
        self.file_writer(RUN_TESTS_SCRIPT_FILE, result)

class TestScriptRunner:
    """
    TestScriptRunner has two collaborators:
    cmdrunner, runs a specified command line, returns stderr as string
    analyzer, analyses unittest-output into green,total number of tests
    """
    def __init__(self, cmdrunner, analyzer):
        self.cmdrunner = cmdrunner
        self.analyzer = analyzer

    def run(self, test_script):
        """
        Runns the test runner script and returns the analysed output.
        """
        output = self.cmdrunner('python "%s"' % test_script)
        return self.analyzer.analyze(output)

class Analyzer:
    """
    Analyzer
    Analyzes unittest output to find green and total number of tests.
    Collaborators: logger, log messages a written to the log
    """
    def __init__(self, logger):
        self.logger = logger

    def analyze(self, txt):
        """
        Analyses the out put from a unittest and returns a tupple of 
        (passed/green, total)
        """
        if len(txt.strip()) == 0:
            return (0, 0)
        toprow =  txt.splitlines()[0]
        green = toprow.count('.')
        total = len(toprow)
        if green < total:
            self.logger.log(txt)
        return (green, total)

class Logger:
    """
    Logger, remembers log messages.
    """

    def __init__(self):
        self.complete_log = ""

    def log(self, message):
        """
        Adds message to the log
        """
        self.complete_log = self.complete_log + message

    def get_log(self):
        """
        returns the log as a string
        """
        return self.complete_log

    def clear(self):
        """
        clears all entries in the log
        """
        self.complete_log = ""

## Rows above this are unit-tested.
## Rows below this are not unit-tested.


def remove_tmp_files():
    """
    Clean up all tempfiles after us.
    """
    safe_remove(RUN_TESTS_SCRIPT_FILE)
    if os.path.exists(TEMP_FILE_DIR_NAME):
        os.removedirs(TEMP_FILE_DIR_NAME)


atexit.register(remove_tmp_files)

class RealFileInfo(object):
    """
    A adapter to easy finde info of a file.
    """
    @staticmethod
    def get_size(filename):
        "returns the size of a file"
        return os.stat(filename).st_size
    @staticmethod
    def get_modified_time(filename):
        "returns the time the file was last modified"
        return os.stat(filename).st_mtime
    @staticmethod
    def get_name_hash(path):
        """
        returns a hash of the name of the path
        """
        return hash(path)

def find_monitored_files():
    " Finds all python modules in current directory and subdirectories "
    monitored_files = []
    for path, _folders, files in os.walk("."):
        for filename in files:
            if re_complete_match(PYTHON_FILE_REGEXP, filename):
                monitored_file = os.path.join(path, filename)
                monitored_files.append(monitored_file)
    return monitored_files
    
def find_test_files_recursively():
    """
    Scan recursively for unit test files in current folder
    and in folders which are packages. Packages are assumed
    to contain the word 'test'. The same holds true for unit
    test files, with the additional condition that they are
    assumed to end with '.py'.
    """
    test_files = []
    for path, folders, files in os.walk("."):
        for filename in files:
            if re_complete_match(TEST_FILE_REGEXP, filename):
                test_file = os.path.join(path, filename)
                test_files.append(test_file)
        folders[:] = [
            folder
            for folder in folders
            if os.path.isfile(
                os.path.join(path, folder, "__init__.py")
            )
        ]
    return test_files

def finder_with_fixed_fileset(fileset):
    """
    Module finder which always returns the
    same file list.
    """
    def find():
        "returns the sent-in file set"
        return fileset
    return find

def safe_remove(path):
    "removes path and ignores all exceptions."
    try: 
        os.unlink(path)
    except OSError: 
        pass

def run_cmdline(cmdline):
    "runs a cmd and returns its output"
    lst = shlex.split(cmdline)
    use_shell = True if ON_WINDOWS else False
    cmd = Popen(lst, stdout=PIPE, stderr=STDOUT, shell=use_shell)
    output = cmd.communicate()[0]
    if os.path.exists(TEMP_OUT_FILE_NAME):
        output = open(TEMP_OUT_FILE_NAME).read()
        os.remove(TEMP_OUT_FILE_NAME)
    if ON_PYTHON3:
        return str(output, 'utf-8')
    else:
        return output

def write_file(filename, content):
    """
    Writes a string of text to a file, overwriting
    any previous file with the same name.
    """
    f_hand = open(filename, 'w')
    f_hand.write(content)
    f_hand.close()

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

class PytddmonFrame(tk.Frame):
    "The Main GUI of pytddmon"

    def __init__(self, root=None, files=None, test_mode=False):
        tk.Frame.__init__(self, root)
        self.button = None
        self.test_mode = test_mode
        self.master.title("pytddmon")
        self.master.resizable(0, 0)
        self.create_button()
        self.grid()
        self.failures = 0
        self.last_checksum = None # important to be different from any number
        self.num_tests = 0
        self.num_tests_prev = 0
        self.num_tests_diff = 0
        self.logger = Logger()
        self.color_picker = ColorPicker()
        self.runner = TestScriptRunner(run_cmdline, Analyzer(self.logger))
        self.monitoring = os.getcwd()

        finder = None
        if files != None:
            self.monitoring = ' '.join(files)
            finder = finder_with_fixed_fileset(files)
        else:
            finder = find_test_files_recursively

        self.script_writer = ScriptWriter(
            finder, 
            write_file, 
            build_run_script
        )
        self.color_table = {
            (True, 'green'): '0f0',
            (False, 'green'): '0c0',
            (True, 'red'): 'f00',
            (False, 'red'): 'c00',
            (True, 'gray'): '999',
            (False, 'gray'): '555'
        }
        self.look_for_changes()

    @staticmethod
    def compute_checksum():
        "returns the checksum for all the sourcefiles as a single integer."
        files = find_monitored_files()
        try:
            files.remove(RUN_TESTS_SCRIPT_FILE)
        except ValueError:
            pass
        return calculate_checksum(files, RealFileInfo())

    def get_number_of_failures(self):
        """Returns the number of faild tests"""
        self.script_writer.write_script()
        (green, total) = self.runner.run(RUN_TESTS_SCRIPT_FILE)
        self.num_tests_prev = self.num_tests
        self.num_tests = total
        return total - green

    @staticmethod
    def clock_string():
        "Formating the time for better readability"
        return strftime("%H:%M:%S", gmtime())

    def create_button(self):
        "Initialize the Button label."
        button_width = 8
        if not ON_WINDOWS:
            # Hack: Window title cut if button too small!
            button_width = 10
        self.button = tk.Label(self,
            text='pytddmon',
            width=button_width,
            relief='raised',
            font=("Helvetica", 16),
            justify=tk.CENTER,
            anchor=tk.CENTER)
        self.button.bind("<Button-1>", self.button_clicked)
        self.button.pack(expand=1, fill='both')

    def button_clicked(self, _widget):
        "Event method triggerd if the button is clicked."
        msg = "Monitoring: %s\n%s" % (self.monitoring, self.logger.get_log())
        message_window(msg)
        
    def get_green_and_total(self):
        """
        Calculate the green results and returns that together with the 
        total of tests as a tuple.
        """
        return (self.num_tests-self.failures, self.num_tests)

    def update_gui(self):
        "Calls all update methods related to the gui"
        (green, total) = self.get_green_and_total()
        self.update_gui_color(green, total)
        self.update_gui_text(green, total)

    def update_gui_color(self, green, total):
        """
        Calculates the new background color and tells the GUI to switch
        to it.
        """
        self.color_picker.set_result( green, total )
        (light, color) = self.color_picker.pick()
        self.color_picker.pulse()
        rgb = '#' + self.color_table[(light, color)]
        self.button.configure(bg=rgb, activebackground=rgb)
        self.configure(background=rgb)

    def update_gui_text(self, green, total):
        "Updates the text of the Main GUI."
        txt = win_text(
            passing_tests=green,
            total_tests=total
            )
        self.button.configure(text=txt)

    def look_for_changes(self):
        "Look for changes in source files and runs tests if needed."
        newval = self.compute_checksum()
        if newval != self.last_checksum:
            self.last_checksum = newval
            self.logger.clear()
            self.logger.log('[%s] Running all tests...\n' % self.clock_string())
            self.failures = self.get_number_of_failures()
            self.logger.log(
                '[%s] Number of failures: %d\n' % (
                    self.clock_string(),
                    self.failures
                    )
                )
        self.update_gui()
        if self.test_mode:
            file_h = open(TEST_MODE_LOG_FILE, "w")
            (green, total) = self.get_green_and_total()
            lines = [ 'green='+str(green), 'total='+str(total) ]
            file_h.write('\n'.join(lines))
            file_h.close()
            self.master.destroy()
        else:
            self.after(750, self.look_for_changes)

def filter_existing_files(files):
    "simple filtering function checking for existence of files"
    return [f for f in files if os.path.exists(f)]

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
    run()

