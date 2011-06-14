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
KrunoSaho: added always-on-top to the pyTDDmon window
Neppord: print(".") will not screw up test-counting (it did before)
'''

import os
import glob
import sys
import tempfile
from time import gmtime, strftime

on_python3 = lambda : sys.version_info[0]==3

if not on_python3():
    from Tkinter import *
else:
    from tkinter import *

# Constants

RUN_TESTS_SCRIPT_FILE = 'pyTDDmon_tmp.py'
ICON_FILE_NAME = "pyTDDmon_tmp.ico"
TEMP_FILE_DIR_NAME = tempfile.mkdtemp()
TEMP_OUT_FILE_NAME = os.path.join(TEMP_FILE_DIR_NAME, "out")

# End of Constants

def build_run_script(files):
    header =    '''\
import unittest

suite = unittest.TestSuite()
load_module_tests = unittest.defaultTestLoader.loadTestsFromModule

'''
    middle = []
    for filename in files:
        module = filename[:-3]
        middle.append( 'import ' + module)
        middle.append('suite.addTests(load_module_tests(' + module + '))\n')
    footer = '''\
if __name__ == '__main__':
    out = file(%r, "w")
    unittest.TextTestRunner(stream=out).run(suite)
''' % TEMP_OUT_FILE_NAME

    return header + "\n".join(middle) + footer

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
        output = self.cmdrunner.run_cmdline('python '+test_script)
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
    safe_remove(ICON_FILE_NAME)

from atexit import register
register(remove_tmp_files)

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
        list = cmdline.split()
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
    label=Label(win, text=message, justify='left', bg=white, activebackground=white)
    label.pack(expand=1,fill='both')

class pyTDDmonFrame(Frame):

    def __init__(self, root=None, files=None):
        Frame.__init__(self, root)
        #self.configure(bg='black')
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
        if files != None:
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
        self.run()

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
        message_window(self.logger.get_log())

    def run(self):
        print("")
        print(" _______________________________________")
        print("|       pyTDDmon window opened          |")
        print("|_______________________________________|")
        print("|                                       |")
        print("| Left click pyTDDmon: show test output |")
        print('|_______________________________________|')
        print(' Monitoring path: ' +  os.getcwd())

    def update_gui(self):
        (green, total, prev_total) = (self.num_tests-self.failures, self.num_tests, self.num_tests_prev)
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
        lines = [
           win_text(passing_tests = green, total_tests = total, prev_total_tests = prev_total),
  #         "",
#           "   Monitoring: " + os.path.join(os.getcwd(), '*.py   '),
        ]
        txt = '\n'.join(lines)
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
        self.after(750, self.look_for_changes)

def file_exists(f):
    try:
        o = open(f, "r")
        o.close()
    except:
        print(f + " does not exist")
        return False
    print(f + " exists")
    return True

def filter_existing_files(files):
    return [f for f in files if file_exists(f)]

def run():
    filtered = filter_existing_files(sys.argv[1:])
    root = Tk()
    if len(filtered)>0:
        app = pyTDDmonFrame(root, filtered)
    else:
        app = pyTDDmonFrame(root)
    app.master.title("pyTDDmon")
    app.master.resizable(0,0)
    app.look_for_changes()
    root.wm_attributes("-topmost", 1)
    if on_windows():
        root.attributes("-toolwindow", 1)
    #try_set_window_icon(root)
    try:
        root.mainloop()
    except Exception as e:
        print(e)
    finally:
        if os.path.exists(TEMP_FILE_DIR_NAME):
            os.removedirs(TEMP_FILE_DIR_NAME)

if __name__ == '__main__':
    run()
