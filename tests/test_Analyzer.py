# coding: utf-8
import unittest
from pytddmon import Analyzer

class test_Analyzer(unittest.TestCase):
    class FakeLog:
        def __init__(self):
            self.received_log_message = None
        
        def log(self, message):
            self.received_log_message = message
    
    def setUp(self):
        self.fake_log = self.FakeLog()
        self.analyzer = Analyzer(self.fake_log)
        
    def test_empty_output_does_not_throw(self):
        self.analyzer.analyze('')
        
    def test_real_input(self):
        txt = '''\
..F.........
======================================================================
FAIL: test_returns_output_from_analyzer (test_running_tests.test_Runner)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/olof/prj/pytddmon/test_running_tests.py", line 94, in test_returns_output_from_analyzer
    self.assertEqual(output, (1,3))
AssertionError: (1, 2) != (1, 3)

----------------------------------------------------------------------
Ran 12 tests in 0.055s

FAILED (failures=1)
'''
        output = self.analyzer.analyze(txt)
        self.assertEqual(output, (11, 12))
        
    def test_no_greens(self):
        output = self.analyzer.analyze('FF')
        self.assertEqual(output, (0, 2))
        
    def test_all_green_means_no_log_message(self):
        self.analyzer.analyze('...\nsoisdid')
        log_message = self.fake_log.received_log_message
        no_log_message = log_message == None
        self.assertTrue(no_log_message)
        
    def test_one_failing_test_means_whole_text_logged(self):
        to_analyze = ".F.\n123something\n"
        self.analyzer.analyze(to_analyze)
        output = self.fake_log.received_log_message
        self.assertEqual(to_analyze, output)

