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

    def test_runs_tests_at_boot(self):
        calls = []
        def fake_filefinder():
            calls.append(1)
            return []
        class FakeMonitor:
            def __init__(self, filefinder):
                pass
            def look_for_changes(self):
                return False
        fake_monitor = FakeMonitor(fake_filefinder)
        pytddmon = Pytddmon(fake_filefinder, fake_monitor)
        pytddmon.main()
        test_runs = len(calls)
        self.assertEqual(1, test_runs)

if __name__ == '__main__':
    unittest.main()
