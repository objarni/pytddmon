#coding: utf-8

'''
Copyright (c) 2010 Olof Bjarnason

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
'''

from Tkinter import *
import sys
import os
import glob

from time import gmtime, strftime

run_tests_script_file = 'pyTDDmon_tmp.py'
icon_file = "pyTDDmon_tmp.ico"

def build_run_script(files):
    header =    '''\
import unittest

suite = unittest.TestSuite()
load_module_tests = unittest.defaultTestLoader.loadTestsFromModule

'''
    middle = ""
    for filename in files:
        module = filename[:-3]
        middle += 'import ' + module + '\n'
        middle += 'suite.addTests(load_module_tests(' + module + '))\n\n'
    footer = '''\
if __name__ == '__main__':
    unittest.TextTestRunner().run(suite)
'''

    return header + middle + footer

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

    def set_result(self, (green, total)):
        old_color = self.color
        self.color = 'green'
        if green == total-1:
            self.color = 'red'
        if green < total-1:
            self.color = 'gray'
        if self.color != old_color:
            self.reset_pulse()

def win_text(total_tests, passing_tests=0, prev_total_tests=0):
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
        result = self.script_builder.build_script_from_modules(self.finder.find_modules())
        self.file_writer.write_file(run_tests_script_file, result)

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

def remove_tmp_files():
    safe_remove(run_tests_script_file)
    safe_remove(icon_file)

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
        p = Popen(list, stdout=PIPE, stderr=STDOUT)
        return p.communicate()[0]

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
    win.title('Log')
    white = '#ffffff'
    label=Label(win, text=message, bg=white, activebackground=white)
    label.pack()

class pyTDDmonFrame(Frame):

    def __init__(self, root=None, files=None):
        Frame.__init__(self, root)
        self.grid()
        self.create_button()
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
        try: files.remove(run_tests_script_file)
        except: pass
        return calculate_checksum(files, RealFileInfo())

    def get_number_of_failures(self):
        self.script_writer.write_script()
        (green, total) = self.runner.run(run_tests_script_file)
        self.num_tests_prev = self.num_tests
        self.num_tests = total
        return total - green

    def clock_string(self):
        return strftime("%H:%M:%S", gmtime())

    def create_button(self):
        self.button = Label(self, text = 'pyTDDmon')
        self.button.bind("<Button-1>", self.button_clicked)
        self.button.grid()

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
        self.color_picker.set_result( (green, total) )
        (light, color) = self.color_picker.pick()
        self.color_picker.pulse()
        rgb = '#' + self.color_table[(light, color)]
        self.button.configure(bg=rgb, activebackground=rgb)

    def update_gui_text(self, green, total, prev_total):
        lines = [
           win_text(passing_tests = green, total_tests = total, prev_total_tests = prev_total),
           "",
           "   Monitoring: " + os.path.join(os.getcwd(), '*.py   '),
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

def try_set_window_icon(root):
    # This feature is only available on Windows for now
    import platform
    if platform.system() != "Windows":
        return

    def create_ico_file():
        data = """  AAABAAEAEBAAAAAAIABoBAAAFgAAACgAAAAQAAAAIAAAAAEAIAAAAAAAQAQAAAAAAAAAAAAAAAAA
                    AAAAAAD///8B////Af///wH///8B////AQAAkjEAAIATFWQUmw9qD4kUZhJxF14XRf///wH///8B
                    ////Af///wH///8B////Af///wH///8BAACPEQAAqJsAAMXzAAC0zRdNRFsIfQjdAIAA/wJ8Av0M
                    bwzBFWUVMf///wH///8B////Af///wH///8BFhaoUwYGu9kAANT/AADU/wAA1P8AALjRFk1HXQh/
                    COEAggD/AIAA/whzCN0WZhJH////Af///wH///8BQkKqGxsbxt8FBdX/AADU/wAA1P8AANT/AADU
                    /wAAuNMiZi9xAYwB/wCFAP8AgAD/B3cG5xVkEUv///8B////AUhIwqsnJ93/GBja/w0N1/8CAtX/
                    AADU/wAA1P8AANT/CQ2Vcw6NDusAkQD/AIgA/wCAAP8Nbguz////AXR0wE1cXOX7PT3j/yws3/8h
                    Idz/Fhba/wsL1/8AANT/AADU/wMDq5UdkhzNAJ0A/wCUAP8AiwD/BXsE8xdjFy1/f86DdXXu/2Ji
                    6v9AQOT/NTXh/yoq3/8eHtz/ExPZ/w4Oy+86dGB3CK8I+wCpAP8AoAD/AJcA/wCOAP8Qbg6PjY3b
                    pYqK8v+Hh/H/Y2Pr/0hI5v89PeP/MjLh/ycn3v8tL7qZM7MzwwC/AP8AtgD/AKwA/wCjAP8AmgD/
                    EHgOo6Oj4qGbm/f/lZX1/42N8v9sbO3/UVHo/0ZG5v9FRdPjYa5uewbSBv8AywD/AMIA/wC4AP8A
                    rwD/AKYA/xeGFqe0tOSPpqb6/6Sk+P+cnPb/lJT0/3R07/9aWur/b2/FiTrZOtUA4AD/ANcA/wDO
                    AP8AxQD/ALsA/wCyAP8kjSSJwsLbVbS0+/2zs/z/qqr6/6Ki+P+amvX/kpLk2WnRa4UB9gH/AOwA
                    /wDjAP8A2gD/ANEA/wDIAP8Huwf/QopCR////wG9vezJv7///7m5/v+xsfv/qan5/7u76rl85ny7
                    CP8I/wD5AP8A7wD/AOYA/wDdAP8A1AD/NLM0vf///wH///8Bv7/dTbm5+e+/v///v7///7i4/f/K
                    yvGxiOmIwzz/PP8X/xf/APwA/wDyAP8A6QD/IdMh62SsZC////8B////Af///wG9vd9hu7v587+/
                    //+/v///ysry3dLn0m1g82DvQP9A/yP/I/8A/wD/L+Uv4W3HbVP///8B////Af///wH///8B////
                    AcTE3TW8vOu3urr7/b29///Q0O7Hq+Srl0P5Q/s+8T7vUN1Qs4LKgiv///8B////Af///wH///8B
                    ////Af///wH///8B////AcfH10G/v+Bzvb3kl8TE2UuHxodJk7qTG////wH///8B////Af///wH/
                    //8BAAD//wAA//8AAP//AAD//wAA//8AAP//AAD//wAA//8AAP//AAD//wAA//8AAP//AAD//wAA
                    //8AAP//AAD//w==
               """
        import base64
        ico = base64.b64decode(data)
        f = open(icon_file, "wb")
        f.write(ico)
        f.close()

    if not os.path.exists(icon_file):
        create_ico_file()
    root.wm_iconbitmap(icon_file)

def filter_existing_files(files):
    return [f for f in files if file_exists(f)]

if __name__ == '__main__':
    filtered = filter_existing_files(sys.argv[1:])
    root = Tk()
    if len(filtered)>0:
        app = pyTDDmonFrame(root, filtered)
    else:
        app = pyTDDmonFrame()
    app.master.title("pyTDDmon")
    app.master.resizable(0,0)
    app.look_for_changes()
    root.wm_attributes("-topmost", 1)
    try_set_window_icon(root)
    try:
        root.mainloop()
    except Exception as e:
        print(e)
