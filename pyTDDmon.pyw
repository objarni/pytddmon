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

'''

''' CONTRIBUTIONS
Fredrik Wendt: help with Tkinter implementation (replacing the pygame dependency)
KrunoSaho: added always-on-top to the pyTDDmon window
Neppord: print(".") will not screw up test-counting (it did before)
'''

import os
import glob
import sys
import tempfile
import atexit
import shlex

from time import gmtime, strftime

on_python3 = lambda : sys.version_info[0]==3

if not on_python3():
    from Tkinter import Tk, Frame, Toplevel, Label, CENTER
else:
    from tkinter import Tk, Frame, Toplevel, Label, CENTER

# Constants

TEMP_FILE_DIR_NAME = tempfile.mkdtemp()
RUN_TESTS_SCRIPT_FILE = os.path.join(TEMP_FILE_DIR_NAME, 'pyTDDmon_tmp.py')
TEMP_OUT_FILE_NAME = os.path.join(TEMP_FILE_DIR_NAME, "out")
# If pyTDDmon is run in test mode, it will:
# 1. display the GUI for a very short time
# 2. write a log file, containing the information displayed (most notably green/total)
# 3. exit
TEST_MODE = False
TEST_MODE_FLAG = '--log-and-exit'
TEST_MODE_LOG_FILE = 'pyTDDmon.log'


# End of Constants

def file_name_to_module(file_name):
    """
    >>> print(file_name_to_module("pyTDDmon.pyw"))
    pyTDDmon
    >>> print(file_name_to_module("pyTDDmon.py"))
    pyTDDmon
    """
    return ".".join(file_name.split(".")[:-1])

def build_run_script(files):
    """
    >>> print(build_run_script(["pyTDDmon.py"]))
    import sys
    import unittest
    import doctest
    ...
    import pyTDDmon
    suite.addTests(load_module_tests(pyTDDmon))
    try:
        suite.addTests(doctest.DocTestSuite(pyTDDmon, optionflags=doctest.ELLIPSIS))
    except:pass
    ...
    """

    content = []
    content.append("import sys")
    content.append("import unittest")
    content.append("import doctest")
    content.append("")
    content.append("sys.path.append(%r)" % os.getcwd())
    content.append("suite = unittest.TestSuite()")
    content.append("load_module_tests = unittest.defaultTestLoader.loadTestsFromModule")
    content.append("")

    for filename in files:
        module = file_name_to_module(filename)
        content.append('import ' + module)
        content.append('suite.addTests(load_module_tests(' + module + '))')
        content.append('try:')
        content.append('    suite.addTests(doctest.DocTestSuite(' + module + ', optionflags=doctest.ELLIPSIS))')
        content.append('except:pass')
        content.append('')
    
    content.append("if __name__ == '__main__':")
    content.append("    out = file(%r, 'w')" % TEMP_OUT_FILE_NAME)
    content.append("    unittest.TextTestRunner(stream=out).run(suite)")

    return "\n".join(content)

def calculate_checksum(filelist, fileinfo):
    val = 0
    for f in filelist:
        val += fileinfo.get_modified_time(f) + fileinfo.get_size(f) + fileinfo.get_name_hash(f)
    return val

class ColorPicker:
    ''' ColorPicker decides the background color the pyTDDmon window,
        based on the number of green tests, and the total number of
        tests. Also, there is a "pulse" (light color, dark color),
        to increase the feeling of continous testing.'''

    def __init__(self):
        self.color = 'green'
        self.reset_pulse()

    def pick(self):
        return (self.light, self.color)

    def pulse(self):
        self.light = not self.light

    def reset_pulse(self):
        self.light = True

    def set_result(self, green, total):
        old_color = self.color
        self.color = 'green'
        if green == total-1:
            self.color = 'red'
        if green < total-1:
            self.color = 'gray'
        if self.color != old_color:
            self.reset_pulse()

def win_text(total_tests, passing_tests=0, prev_total_tests=0):
    return "%d/%d" % (passing_tests, total_tests)
    if prev_total_tests > total_tests:
        return "%d of %d tests green\n"% (passing_tests, total_tests) +\
                     "Warning: number of tests decreased!"
    if total_tests == 0:
        return "No tests found!"
    if passing_tests == total_tests:
        return "All %d tests green" % total_tests
    txt = "%d of %d tests green"
    if passing_tests+1 < total_tests:
        txt = "Warning: only " + txt + "!"
    return txt % (passing_tests, total_tests)

class ScriptWriter:
    '''
    ScriptWriter: gets it's modules from the Finder, and
    writes a test script using the FileWriter+script_builder
    '''
    def __init__(self, finder, file_writer, script_builder):
        self.finder = finder
        self.file_writer = file_writer
        self.script_builder = script_builder

    def write_script(self):
        modules = self.finder.find_modules()
        result = self.script_builder.build_script_from_modules(modules)
        self.file_writer.write_file(RUN_TESTS_SCRIPT_FILE, result)

class TestScriptRunner:
    ''' TestScriptRunner -
      Collaborators:
       CmdRunner, runs a specified command line, returns stderr as string
       Analyzer, analyses unittest-output into green,total number of tests
    '''
    def __init__(self, cmdrunner, analyzer):
        self.cmdrunner = cmdrunner
        self.analyzer = analyzer

    def run(self, test_script):
        output = self.cmdrunner.run_cmdline('python "%s"' % test_script)
        return self.analyzer.analyze(output)

class Analyzer:
    '''
    Analyzer
    Analyserar unittest-output efter gröna test, och antal test.
    Medarbetare: Log, dit loggmeddelande skrivs.
    '''
    def __init__(self, logger):
        self.logger = logger

    def analyze(self, txt):
        if len(txt.strip()) == 0:
            return (0, 0)
        toprow =  txt.splitlines()[0]
        green = toprow.count('.')
        total = len(toprow)
        if green<total:
            self.logger.log(txt)
        return (green, total)

class Logger:
    ''' Logger, remembers log messages.'''

    def __init__(self):
        self.clear()

    def log(self, message):
        self.complete_log = self.complete_log + message

    def get_log(self):
        return self.complete_log

    def clear(self):
        self.complete_log = ""

## Rows above this are unit-tested.
## Rows below this are not unit-tested.

def on_windows():
    import platform
    return platform.system() == "Windows"

def remove_tmp_files():
    safe_remove(RUN_TESTS_SCRIPT_FILE)
    if os.path.exists(TEMP_FILE_DIR_NAME):
        os.removedirs(TEMP_FILE_DIR_NAME)


atexit.register(remove_tmp_files)

class RealFileInfo:
    def get_size(self, f):
        return os.stat(f).st_size
    def get_modified_time(self, f):
        return os.stat(f).st_mtime
    def get_name_hash(self, path):
        hash = 0
        for ch in path:
            hash += ord(ch)
        return hash

class Finder:
    def find_modules(self):
        return glob.glob("test_*.py")

class FinderWithFixedFileSet:
    def __init__(self, files):
        self.files = files

    def find_modules(self):
        return self.files

def safe_remove(path):
    try: os.unlink(path)
    except: pass

class CmdRunner:
    def run_cmdline(self, cmdline):
        from subprocess import Popen, PIPE, STDOUT
        list = shlex.split(cmdline)
        use_shell = True if on_windows() else False
        p = Popen(list, stdout=PIPE, stderr=STDOUT, shell=use_shell)
        bytes = p.communicate()[0]
        if os.path.exists(TEMP_OUT_FILE_NAME):
            bytes = file(TEMP_OUT_FILE_NAME).read()
            os.remove(TEMP_OUT_FILE_NAME)
        if on_python3():
            return str(bytes, 'utf-8')
        else:
            return bytes

class FileWriter:
    def write_file(self, filename, content):
        f = open(filename, 'w')
        f.write(content)
        f.close()

class ScriptBuilder:
    def build_script_from_modules(self, modules):
        return build_run_script(modules)

def message_window(message):
    win = Toplevel()
    win.wm_attributes("-topmost", 1)
    if on_windows():
        win.attributes("-toolwindow", 1)
    win.title('Details')
    white = '#ffffff'
    message = message.replace('\r\n', '\n')
    label = Label(win, text=message, justify='left', bg=white, activebackground=white)
    label.pack(expand=1,fill='both')

class pyTDDmonFrame(Frame):

    def __init__(self, root=None, files=None):
        Frame.__init__(self, root)
        self.master.title("pyTDDmon")
        self.master.resizable(0,0)
        self.create_button()
        self.grid()
        self.failures = 0
        self.last_checksum = 0
        self.num_tests = 0
        self.num_tests_prev = 0
        self.num_tests_diff = 0
        self.logger = Logger()
        self.color_picker = ColorPicker()
        self.runner = TestScriptRunner(CmdRunner(), Analyzer(self.logger))
        finder = Finder()
        self.monitoring = os.getcwd()
        if files != None:
            self.monitoring = ' '.join(files)
            finder = FinderWithFixedFileSet(files)
        self.script_writer = ScriptWriter(finder, FileWriter(), ScriptBuilder())
        self.color_table = {
            (True, 'green'): '0f0',
            (False, 'green'): '0c0',
            (True, 'red'): 'f00',
            (False, 'red'): 'c00',
            (True, 'gray'): '999',
            (False, 'gray'): '555'
        }
        self.look_for_changes()

    def compute_checksum(self):
        files = glob.glob('*.py')
        try: files.remove(RUN_TESTS_SCRIPT_FILE)
        except: pass
        return calculate_checksum(files, RealFileInfo())

    def get_number_of_failures(self):
        self.script_writer.write_script()
        (green, total) = self.runner.run(RUN_TESTS_SCRIPT_FILE)
        self.num_tests_prev = self.num_tests
        self.num_tests = total
        return total - green

    def clock_string(self):
        return strftime("%H:%M:%S", gmtime())

    def create_button(self):
        button_width = 8
        if not on_windows():
            # Hack: Window title cut if button too small!
            button_width = 10
        self.button = Label(self,
            text='pyTDDmon',
            width=button_width,
            relief='raised',
            font=("Helvetica", 16),
            justify=CENTER,
            anchor=CENTER)
        self.button.bind("<Button-1>", self.button_clicked)
        self.button.pack(expand=1,fill='both')

    def button_clicked(self, widget):
        msg = "Monitoring: %s\n%s" % (self.monitoring, self.logger.get_log())
        message_window(msg)
        
    def get_green_and_total(self):
        return (self.num_tests-self.failures, self.num_tests)

    def update_gui(self):
        (green, total) = self.get_green_and_total()
        prev_total = self.num_tests_prev
        self.update_gui_color(green, total)
        self.update_gui_text(green, total, prev_total)

    def update_gui_color(self, green, total):
        self.color_picker.set_result( green, total )
        (light, color) = self.color_picker.pick()
        self.color_picker.pulse()
        rgb = '#' + self.color_table[(light, color)]
        self.button.configure(bg=rgb, activebackground=rgb)
        self.configure(background=rgb)

    def update_gui_text(self, green, total, prev_total):
        txt = win_text(passing_tests = green, total_tests = total, prev_total_tests = prev_total)
        self.button.configure(text=txt)

    def look_for_changes(self):
        newval = self.compute_checksum()
        if newval != self.last_checksum:
            self.last_checksum = newval
            self.logger.clear()
            self.logger.log('[%s] Running all tests...\n' % self.clock_string())
            self.failures = self.get_number_of_failures()
            self.logger.log('[%s] Number of failures: %d\n' % (self.clock_string(), self.failures))
        self.update_gui()
        if TEST_MODE:
            f = open(TEST_MODE_LOG_FILE, "w")
            (green, total) = self.get_green_and_total()
            lines = [ 'green='+str(green), 'total='+str(total) ]
            f.write('\n'.join(lines))
            f.close()
            self.master.destroy()
        else:
            self.after(750, self.look_for_changes)

def filter_existing_files(files):
    return [f for f in files if os.path.exists(f)]

def run():
    # Command line argument handling
    args = list(sys.argv[1:])
    if TEST_MODE_FLAG in args:
        global TEST_MODE
        TEST_MODE = True
        args.remove(TEST_MODE_FLAG)
    filtered = filter_existing_files(args)
    
    # Basic tkinter initialization
    root = Tk()
    root.wm_attributes("-topmost", 1)
    if on_windows():
        root.attributes("-toolwindow", 1)
       
    # Create main window
    if len(filtered)>0:
        win = pyTDDmonFrame(root, filtered)
    else:
        win = pyTDDmonFrame(root)

    # Main loop
    try:
        root.mainloop()
    except Exception as e:
        print(e)

if __name__ == '__main__':
    run()

