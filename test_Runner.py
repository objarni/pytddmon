# coding: utf-8
import unittest
from pyTDDmon import TestScriptRunner

class test_TestScriptRunner(unittest.TestCase):
	class FakeAnalyzer:
		def __init__(self):
			self.output = (0,0)
		
		def analyze(self, txt):
			self.received_input = txt
			return self.output
		
		def set_output(self, output):
			self.output = output

	class FakeCmdRunner:
		def __init__(self):
			self.received_cmdline = ''
			self.stderr_output = ''
		
		def run_cmdline(self, cmdline):
			self.received_cmdline = cmdline
			return self.stderr_output
	
		def set_stderr_output(self, txt):
			self.stderr_output = txt

	def setUp(self):
		self.fake_cmdrunner = self.FakeCmdRunner()
		self.fake_analyzer = self.FakeAnalyzer()
		self.runner = TestScriptRunner(self.fake_cmdrunner, self.fake_analyzer)

	def test_sends_correct_commandline_to_cmdrunner(self):
		self.assertSentCommandLine('test_module.py', 'python "test_module.py"')
		self.assertSentCommandLine('test_module2.py', 'python "test_module2.py"')

	def assertSentCommandLine(self, module, expected_cmdline):
		self.runner.run(module)
		cmdline = self.fake_cmdrunner.received_cmdline
		self.assertEqual(cmdline, expected_cmdline)
		
	def test_sends_output_from_cmdrunner_to_analyzer(self):
		self.fake_cmdrunner.set_stderr_output('123')
		self.runner.run('test_module.py')
		analyzer_input = self.fake_analyzer.received_input
		self.assertEqual(analyzer_input, "123")
		
	def test_returns_output_from_analyzer(self):
		self.fake_analyzer.set_output((1,2))
		output = self.runner.run('test_something.py')
		self.assertEqual(output, (1,2))

