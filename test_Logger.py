# coding: utf-8
import unittest
from pyTDDmon import Logger

class test_Logger(unittest.TestCase):
	def test_concatenates_log_messages(self):
		logger = Logger()
		logger.log("abc\n")
		logger.log("def\n")
		complete_log = logger.get_log()
		self.assertEqual(complete_log, "abc\ndef\n")
		
	def test_clear_removes_old_log_messages(self):
		log = Logger()
		log.log("test")
		log.clear()
		self.assertEqual("", log.get_log())

