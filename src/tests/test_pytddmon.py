# coding: utf-8
import unittest
from pytddmon import Pytddmon

'''
- kör tester från början
- kör inte tester om ingen förändring
- kör tester om förändring
- summa finns i .total_tests
- gröna finns i .total_passed_tests
'''

class test_Pytddmon(unittest.TestCase):
    def test_number_of_tests_variable(self):
        return
        pytddmon.main()
        number_of_tests = pytddmon.total_tests
        assert number_of_tests == 3
        
    def test_runs_tests_at_boot(self):
        return
        tests_run
        def fake_detector(): pass
        pytddmon = Pytddmon(fake_detector, fake_file_finder)
        pytddmon.main()
        assert tests_run

if __name__ == '__main__':
    unittest.main()
