#! /usr/bin/env python
#coding: utf-8

'''
COPYRIGHT (c) 2009, 2010, 2011
.. in order of first contribution
Olof Bjarnason
    Initial proof-of-concept pygame implementation.
Fredrik Wendt:
    Help with Tkinter implementation (replacing the pygame dependency)
KrunoSaho
    Added always-on-top to the pytddmon window
Neppord(Samuel Ytterbrink)
    Print(".") will not screw up test-counting (it did before)
    Docstring support
    Recursive discovery of tests
    Refactoring to increase Pylint score from 6 to 9.5 out of 10 (!)
    Numerous refactorings & other improvements
Rafael Capucho
    Python shebang at start of script, enabling "./pytddmon.py" on unix systems
Ilian Iliev
    Use integers instead of floats in file modified time (checksum calc)
    Auto-update of text in Details window when the log changes

LICENSE
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
'''

import os
import sys
import platform
import optparse
import re

ON_PYTHON3 = sys.version_info[0] == 3
ON_WINDOWS = platform.system() == "Windows"

####
## Core
####


class Pytddmon(object):
    """The core class, all functionality are agregated and lives inside this
    class."""
    def __init__(
        self,
        project_name="<pytddmon>",
        file_strategies=None,
        test_strategies=None,
        log_level=None
    ):
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
        self.log_level = log_level
        self.test_logger = DefaultLogger()
        self.files_are_changed = False

    def which_files_has_changed(self):
        """Returns list of changed files."""
        changed_files = []
        for file_strategy in self.file_strategies:
            changed_files.extend(file_strategy.which_files_has_changed())
        return changed_files

    def run_tests(self, file_paths=None):
        """Runs all tests and updates the time it took and the total test run
        and passed."""
        import time
        file_paths = file_paths if file_paths != None else []
        start = time.time()
        self.total_tests_run = 0
        self.total_tests_passed = 0
        self.test_logger = DefaultLogger()
        for test_strategy in self.test_strategies:
            passed, tests_run = test_strategy.run_tests(file_paths, logger=self.test_logger)
            self.total_tests_run += tests_run
            self.total_tests_passed += passed
        self.last_testrun_time = time.time() - start

    def main(self):
        """This is the main loop body"""
        file_paths = self.which_files_has_changed()
        self.files_are_changed = False
        if file_paths != []:
            self.files_are_changed = True
            self.run_tests(file_paths)

    def get_logs(self):
        """Creates a readabel log of the all test strategies run"""
        log = self.test_logger.getlog(self.log_level)
        return log

class Monitor:
    def __init__(self, file_finder, get_file_size, get_file_modtime):
        self.file_finder = file_finder
        self.get_file_size = get_file_size
        self.get_file_modtime = get_file_modtime
        self.snapshot = self.get_snapshot()

    def get_snapshot(self):
        snapshot = {}
        for file in self.file_finder():
            file_size = self.get_file_size(file)
            file_modtime = self.get_file_modtime(file)
            snapshot[file] = (file_size, file_modtime)
        return snapshot

    def look_for_changes(self):
        print "\nused to be: " + str(self.snapshot)
        new_snapshot = self.get_snapshot()
        change_detected = new_snapshot != self.snapshot
        self.snapshot = new_snapshot
        print "now is: " + str(new_snapshot)
        return change_detected

class DefaultLogger(object):
    """class that handels accumulation of logs. It also take care of tagging
    logs so that you can query for specific log messages."""
    levels = {
        None: int("1111",2),
        "info": int("1",2),
        "warning": int("10",2),
        "error": int("100",2),
        "debug": int("1000",2),
        "all": int("1111",2)
    }

    levels_back = dict(
        (value, key)
        for key, value in levels.items() if key!=None
    )

    def __init__(self):
        # loggs is a list with int keys and list with strings as values
        self.loggs = []

    def getlog(self, level=None):
        level = self.level_2_int(level)
        return "\n".join(
            "[%s]%s" % (
                self.int_2_level(level_),
                log
            )
            for level_, log in self.loggs if level_ & level
        )

    @classmethod
    def level_2_int(cls, level=None):
        return cls.levels.get(level, level)
    @classmethod
    def int_2_level(cls, level):
        return cls.levels_back.get(level, "Un Known")

    def log(self, log, level=None):
        level = self.level_2_int(level)
        self.loggs.append(
            (level, log)
        )
            
        
    
####
## Hashing
####


class DefaultHasher(object):
    """A simple hasher which takes the size and the modified time and returns
    a checksum."""
    def __init__(self, os_module):
        self.os_module = os_module
        self.os_module.stat_float_times(False)
        
    def __call__(self, file_path):
        """Se Class description."""
        stat = self.os_module.stat(file_path)
        return stat.st_size + (stat.st_mtime * 1j) + hash(file_path)


####
## File Strategies
####


class StaticFileStartegy(object):
    """Looks for changes in a static set of files."""
    def __init__(self, file_paths, hasher=DefaultHasher(os)):
        self.file_paths = None
        self.last_hash = None
        self.change_file_set(file_paths)
        self.hasher = hasher

    def change_file_set(self, file_paths):
        """Used to change what set of files are monitored for change"""
        self.file_paths = set([
            os.path.abspath(file_path) for file_path in file_paths
        ])
        self.last_hash = [-1] * len(self.file_paths)

    def which_files_has_changed(self):
        """Looks through all file paths and return which of them has changed.
        """
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
        ret = []
        for file_path in self.file_paths:
            try:
                ret.append(self.hasher(file_path))
            except IOError:
                pass
        return ret


class RecursiveRegexpFileStartegy(object):
    """Looks for files recursively from a root dir with a specific regexp
    pattern."""
    def __init__(self, root, expr, walker=os.walk, hasher=DefaultHasher(os)):
        self.walker = walker
        self.hasher = hasher
        self.root = os.path.abspath(root)
        self.expr = expr
        self.pairs = []

    def get_pairs(self):
        """calculates a new list of (path, hash) pairs"""
        file_paths = set()
        for path, _folder, filenames in self.walker(self.root):
            for filename in filenames:
                if re_complete_match(self.expr, filename):
                    file_paths.add(
                        os.path.abspath(os.path.join(path, filename))
                    )
        return [
            (file_path, self.hasher(file_path)) for file_path in file_paths
        ]

    def which_files_has_changed(self):
        """Looks for files recursively from a root dir with a specific regexp"""
        new_pairs = self.get_pairs()
        new = set(new_pairs)
        old = set(self.pairs)
        paths = new.symmetric_difference(old)
        paths = [path for path, _file_hash in paths]
        self.pairs = new_pairs
        return paths


class RecursiveGlobFileStartegy(RecursiveRegexpFileStartegy):
    """Like the RecursiveRegexpFileStartegy but it takes a glob expr instead of
    a regexp expr"""
    def __init__(self, root, expr, walker=os.walk, hasher=DefaultHasher(os)):
        import fnmatch
        super(RecursiveGlobFileStartegy, self).__init__(
            root=root,
            expr=fnmatch.translate(expr),
            walker=walker,
            hasher=hasher
        )


def log_exceptions(func):
    """Decorator that forwards the error message from an expetion to the log
    slot of the return value and also returnsa a complexnumber to signal that
    the result is an error."""
    from functools import wraps

    @wraps(func)
    def wrapper(*a, **k):
        "Docstring"
        try:
            return func(*a, **k)
        except:
            import traceback
            return (0, 1j, traceback.format_exc())
    return wrapper


####
## Test Runners
####
# These needs to be functions due to that they are going to be called in a
# nother procces and multiprocessing demands that they should be picabel.
####

def StringIO():
    if ON_PYTHON3:
        import io as StringIO
    else:
        import StringIO 
    return StringIO.StringIO()

@log_exceptions
def run_unittests(arguments):
    """Loads all unittests in file, with root as package location."""
    import unittest

    root, file_path = arguments
    module = file_name_to_module(root, file_path)
    err_log = StringIO()
    test_loader = unittest.TestLoader()
    suite = test_loader.loadTestsFromName(module)
    text_test_runner = unittest.TextTestRunner(stream=err_log)
    result = text_test_runner.run(suite)
    return (
        result.testsRun - len(result.failures) - len(result.errors),
        result.testsRun,
        err_log.getvalue()
    )


@log_exceptions
def run_doctests(arguments):
    """Loads all doctests in file, with root as package location."""
    root, file_path = arguments
    import unittest
    import doctest
    module = file_name_to_module(root, file_path)
    err_log = StringIO()
    try:
        suite = doctest.DocTestSuite(module, optionflags=doctest.ELLIPSIS)
    except ValueError:
        return (
        0,
        0,
        """No doctests found in:%r\n""" % (module)  
        )
    text_test_runner = unittest.TextTestRunner(stream=err_log)
    result = text_test_runner.run(suite)
    return (
        result.testsRun - len(result.failures) - len(result.errors),
        result.testsRun,
        err_log.getvalue()
    )


####
## Test Strategies
####


class StaticTestStrategy(StaticFileStartegy):
    """Runs a Static set of files as if thay where Unitttest suits. They must
    however be on the python path or be inside a package that are on the path.
    """
    def __init__(
        self,
        file_paths,
        test_runner,
        hasher=DefaultHasher(os)
    ):
        self.test_runner = test_runner
        super(StaticTestStrategy, self).__init__(
            file_paths=file_paths,
            hasher=hasher
        )

    def run_tests(self, _file_paths, logger, pool=True):
        """Runs all staticly selected files as if they where UnitTests"""
        from multiprocessing import Pool
        file_paths_to_run = []
        for file_path in self.file_paths:
            file_paths_to_run.append((os.getcwd(), file_path))
        if pool:
            pool = Pool()
            results = pool.map(self.test_runner, file_paths_to_run)
        else:
            results = map(self.test_runner, file_paths_to_run)
        all_green = 0
        all_total = 0
        for (green, total, log), (_rt, pth) in zip(results, file_paths_to_run):
            all_green += green
            all_total += total
            if green.imag != 0 or total.imag != 0:
                level = "error"
            elif green == total:
                level = "info"
            else:
                level = "warning"
            logger.log(log, level=level)
        if type(pool) != bool:
            pool.terminate()
        return (all_green, all_total)


class RecursiveRegexpTestStartegy(object):
    """Recursively look for tests in packages with a filename matching the
    regexpr."""
    def __init__(self, root, expr, test_runner, walker=os.walk):
        self.test_runner = test_runner
        self.root = os.path.abspath(root)
        self.expr = expr
        self.walker = walker

    @staticmethod
    def is_package(path, folder):
        """Check if folder is a package"""
        return os.path.isfile(os.path.join(path, folder, "__init__.py"))

    def find_tests(self):
        """Helper method that finds the tests"""
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
                else:
                    pass
        return file_paths_to_run

    def run_tests(self, _file_paths, logger, pool=True):
        """finds and run all tests"""
        from multiprocessing import Pool

        file_paths_to_run = self.find_tests()
        if pool:
            pool = Pool()
            results = pool.map(
                self.test_runner,
                file_paths_to_run
            )
        else:
            results = map(
                self.test_runner,
                file_paths_to_run
            )
        all_green = 0
        all_total = 0
        for (green, total, log), (_rt, pth) in zip(results, file_paths_to_run):
            all_green += green
            all_total += total
            if green.imag != 0 or total.imag != 0:
                level = "error"
            elif green == total:
                level = "info"
            else:
                level = "warning"
            logger.log(log, level=level)
        if type(pool) != bool:
            pool.terminate()
        return (all_green, all_total)


####
## GUI
####


class TkGUI(object):
    """A cloection class for all that is tkinter"""
    def __init__(self, pytddmon):
        self.pytddmon = pytddmon
        self.color_picker = ColorPicker()
        self.tkinter = None
        self.building_tkinter()
        self.root = None
        self.building_root()
        self.title_font = None
        self.button_font = None
        self.building_fonts()
        self.frame = None
        self.building_frame()
        self.button = None
        self.building_button()
        self.frame.grid()
        self.message_window = None
        self.text = None

        if ON_WINDOWS:
            buttons_width = 25
        else:
            buttons_width = 75
        self.root.minsize(
            width=self.title_font.measure(
                self.pytddmon.project_name
            ) + buttons_width, 
            height=0
        )
        self.frame.pack(expand=1, fill="both")

    def building_tkinter(self):
        """imports the tkinter module as self.tkinter"""
        if not ON_PYTHON3:
            import Tkinter as tkinter
        else:
            import tkinter
        self.tkinter = tkinter

    def building_root(self):
        """take hold of the tk root object as self.root"""
        self.root = self.tkinter.Tk()
        self.root.wm_attributes("-topmost", 1)
        if ON_WINDOWS:
            self.root.attributes("-toolwindow", 1)
            print("Minimize me!")

    def building_fonts(self):
        "building fonts"
        if not ON_PYTHON3:
            import tkFont
        else:
            from tkinter import font as tkFont 
        self.title_font = tkFont.nametofont("TkCaptionFont")
        self.button_font = tkFont.Font(name="Helvetica", size=28)

    def building_frame(self):
        """Creates a frame and assigns it to self.frame"""
        # Calculate the width of the tilte + buttons
        self.frame = self.tkinter.Frame(
            self.root
        )
        # Sets the title of the gui
        self.frame.master.title(self.pytddmon.project_name)
        # Forces the window to not be resizeable
        self.frame.master.resizable(False, False)
        self.frame.pack(expand=1, fill="both")

    def building_button(self):
        """Builds  abutton and assign it to self.button"""
        self.button = self.tkinter.Label(
            self.frame,
            text="loading...",
            relief='raised',
            font=self.button_font,
            justify=self.tkinter.CENTER,
            anchor=self.tkinter.CENTER
        )
        self.button.bind(
            "<Button-1>",
            self.display_log_message
        )
        self.button.pack(expand=1, fill="both")

    def window_is_open(self):
        """checks whether the textwdiget windows is open"""
        if not self.message_window or not self.message_window.winfo_exists():
            return False
        return True

    def update(self):
        """updates the tk gui"""
        self.color_picker.set_result(
            self.pytddmon.total_tests_passed,
            self.pytddmon.total_tests_run,
        )
        light, color = self.color_picker.pick()
        rgb = self.color_picker.translate_color(light, color)
        self.color_picker.pulse()
        if self.pytddmon.total_tests_run.imag!=0:
            text = "*%i*" % self.pytddmon.total_tests_run.imag
        else:
            text = "%r/%r" % (
                self.pytddmon.total_tests_passed,
                self.pytddmon.total_tests_run
            )

        self.button.configure(
            bg=rgb,
            activebackground=rgb,
            text=text
        )
        self.root.configure(
            bg=rgb,
        )
        
        if self.pytddmon.files_are_changed and self.window_is_open():
            self.update_text_window()

    def get_text_message(self):
        """returns the logmessage from pytddmon"""
        message = "monitoring: %s\ntime: %.2f seconds\n%s" % (
                self.pytddmon.project_name,
                self.pytddmon.last_testrun_time,
                self.pytddmon.get_logs()
            )
        return message

    def open_text_window(self):
        """creates new window and text widget""" 
        win = self.tkinter.Toplevel()
        win.wm_attributes("-topmost", 1)
        if ON_WINDOWS:
            win.attributes("-toolwindow", 1)
        win.title('Details')
        self.message_window = win
        self.text = self.tkinter.Text(win)

    def update_text_window(self):
        """inserts/replaces the log message in the text widget"""
        text = self.text
        text['state'] = self.tkinter.NORMAL
        text.delete(1.0, self.tkinter.END)
        text.insert(self.tkinter.INSERT, self.get_text_message())
        text.see(self.tkinter.END)
        text['state'] = self.tkinter.DISABLED
        text.pack(expand=1, fill='both')
        text.focus_set()

    def display_log_message(self, _arg):
        """displays the logmessage from pytddmon in a window"""
        if not self.window_is_open():
            self.open_text_window()
            self.update_text_window()

    def loop(self):
        """the main loop"""
        self.pytddmon.main()
        self.update()
        self.frame.after(750, self.loop)

    def run(self):
        """starts the main loop and goes into sleep"""
        self.loop()
        self.root.mainloop()


####
## Un Organized
####


def re_complete_match(regexp, string_to_match):
    """Helper function that does a regexp check if the full string_to_match
    matches the regexp"""
    return bool(re.match(regexp + "$", string_to_match))


def file_name_to_module(base_path, file_name):
    r"""Converts filenames of files in packages to import friendly dot
    separated paths.

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
    >>> print(
    ...     file_name_to_module(
    ...         "/User/pytddmon\\ geek/pytddmon/",
    ...         "/User/pytddmon\\ geek/pytddmon/tests/pytddmon.py"
    ...     )
    ... )
    tests.pytddmon
    """
    symbol_stripped = os.path.relpath(file_name, base_path)
    for symbol in r"/\.":
        symbol_stripped = symbol_stripped.replace(symbol, " ")
    words = symbol_stripped.split()
    # remove .py/.pyw
    module_words = words[:-1]
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
        elif green == total - 1:
            self.color = 'red'
        elif green < total - 1:
            self.color = 'gray'
        if self.color != old_color:
            self.reset_pulse()

    @classmethod
    def translate_color(cls, light, color):
        """helper method to create a rgb string"""
        return "#" + cls.color_table[(light, color)]


def parse_commandline():
    """
    returns (files, test_mode) created from the command line arguments
    passed to pytddmon.
    """
    parser = optparse.OptionParser()
    parser.add_option(
        "--log-and-exit",
        action="store_true",
        default=False,
        help='Run all tests, write the results to "pytddmon.log" and exit.')
    (options, args) = parser.parse_args()
    return (args, options.log_and_exit)


def run():
    """
    The main function: basic initialization and program start
    """
    sys.path[:0] = [os.getcwd()]
    # Command line argument handling
    (static_file_set, test_mode) = parse_commandline()
    file_strategies = []
    if static_file_set:
        file_strategies.append(
            StaticFileStartegy(
                static_file_set
            )
        )
    else:
        file_strategies.append(
            RecursiveGlobFileStartegy(
                root=os.getcwd(),
                expr="*.py"
            )
        )
    test_strategies = []
    if static_file_set:
        test_strategies.append(
            StaticTestStrategy(
                static_file_set,
                test_runner=run_unittests
            )
        )
        test_strategies.append(
            StaticTestStrategy(
                static_file_set,
                test_runner=run_doctests
            )
        )
    else:
        test_strategies.append(
            RecursiveRegexpTestStartegy(
                root=os.getcwd(),
                expr="test_.*\\.py",
                test_runner=run_unittests
            )
        )
        test_strategies.append(
            RecursiveRegexpTestStartegy(
                root=os.getcwd(),
                expr="test_.*\\.py",
                test_runner=run_doctests
            )
        )

    pytddmon = Pytddmon(
        project_name=os.path.basename(os.getcwd()),
        file_strategies=file_strategies,
        test_strategies=test_strategies,
        log_level=DefaultLogger.levels["error"] | DefaultLogger.levels["warning"]
    )
    if test_mode:
        pytddmon.main()
        with open("pytddmon.log", "w") as log_file:
            log_file.write(
                "green=%r\ntotal=%r\n" % (
                    pytddmon.total_tests_passed,
                    pytddmon.total_tests_run
                )
            )
    else:
        TkGUI(pytddmon).run()

if __name__ == '__main__':
    run()
