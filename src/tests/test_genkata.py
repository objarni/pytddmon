import unittest

from pytddmon import Kata

class KataGeneratorTests(unittest.TestCase):
	def setUp(self):
		kata = Kata('bowling')
		self.result = kata.content
		self.filename = kata.filename

	def test_output_includes_kata_name(self):
		self.assertTrue('bowling' in self.result)

	def test_output_imports_unittest(self):
		self.assertTrue('import unittest' in self.result)

	def test_classname_cased_nicely(self):
		self.assertTrue('BowlingTests' in self.result)

	def test_contains_a_test_def(self):
		self.assertTrue('def test_something(self):' in self.result)

	def test_contains_a_true_assertion(self):
		self.assertTrue('self.assertTrue(True)' in self.result)

	def test_contains_an_list_equality_assertion(self):
		self.assertTrue('self.assertEqual([1, 2], [x for x in range(1, 3)])' in self.result)

	def test_removes_spaces_in_name(self):
		result = Kata('a name with spaces').content
		self.assertTrue('ANameWithSpacesTests' in result, result)

	def test_generates_a_nice_filename(self):
		self.assertEqual('test_bowling.py', self.filename)

	def test_filename_is_stripped_from_spaces(self):
		filename = Kata('Blair witch project').filename
		self.assertEqual('test_blair_witch_project.py', filename)
