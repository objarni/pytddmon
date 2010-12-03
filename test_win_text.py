import unittest
from pyTDDmon import win_text

class test_win_text(unittest.TestCase):

	def test_no_tests_exist(self):
		wintext = win_text(total_tests = 0)
		self.assertEqual("No tests found!", wintext)
		
	def test_one_of_one_passing(self):
		wintext = win_text(passing_tests = 1, total_tests = 1)
		self.assertEqual("All 1 tests green", wintext)
		
	def test_one_of_two_passing(self):
		wintext = win_text(passing_tests = 1, total_tests = 2)
		self.assertEqual("1 of 2 tests green", wintext)
		
	def test_one_of_three_passing(self):
		wintext = win_text(passing_tests = 1, total_tests = 3)
		self.assertEqual("Warning: only 1 of 3 tests green!", wintext)

	def test_total_number_of_tests_decreased(self):
		wintext = win_text(passing_tests = 1, total_tests = 2, prev_total_tests = 3)
		self.assertEqual(
			"1 of 2 tests green\nWarning: number of tests decreased!",
			wintext)

