# coding: utf-8
import unittest
from pytddmon import ScriptWriter

class test_ScriptWriter(unittest.TestCase):
	class FakeFinder:
		def __init__(self):
			self.find_modules_returns = []
			
		def __call__(self):
			return self.find_modules_returns
			
	class FakeScriptBuilder:
		def __init__(self):
			self.build_script_from_modules_returns = ''
			
		def build_script_from_modules(self, modules):
			self.received_modules = modules
			return self.build_script_from_modules_returns
			
	class FakeFileWriter:
		def write_file(self, filename, content):
			self.received_content = content
			self.received_filename = filename
			
	def setUp(self):
		self.fake_finder = self.FakeFinder()
		self.fake_file_writer = self.FakeFileWriter()
		self.fake_script_builder = self.FakeScriptBuilder()
		self.script_writer = ScriptWriter(
			self.fake_finder,
			self.fake_file_writer,
			self.fake_script_builder)
			
	def test_sends_found_modules_to_script_builder(self):
		sent_modules = ['a', 'b']
		self.fake_finder.find_modules_returns = sent_modules
		self.script_writer.write_script()
		received_modules = self.fake_script_builder.received_modules
		self.assertEqual(received_modules, sent_modules)
		
	def test_writes_built_script_to_some_file(self):
		build_content = 'abc'
		self.fake_script_builder.build_script_from_modules_returns = build_content
		self.script_writer.write_script()
		written_content = self.fake_file_writer.received_content
		self.assertEqual(written_content, build_content)

