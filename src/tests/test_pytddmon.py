# coding: utf-8
import unittest
from pytddmon import Pytddmon

'''
#- kör tester från början
#- kör inte tester om ingen förändring
#- kör tester om förändring
- summa finns i .total_tests
- gröna finns i .total_passed_tests
'''

class test_Pytddmon_monitor_communication(unittest.TestCase):
    class FakeMonitor:
        def __init__(self, look_for_changes_returns):
            self.returns = list(look_for_changes_returns)
            self.returns.reverse()
        def look_for_changes(self):
            return self.returns.pop()

    def setUp(self):
        self.number_of_test_runs = 0

    def fake_filefinder(self):
        self.number_of_test_runs += 1
        return []
        
    def test_runs_tests_at_boot(self):
        fake_monitor = self.FakeMonitor(look_for_changes_returns = [False])
        pytddmon = Pytddmon(self.fake_filefinder, fake_monitor)
        pytddmon.main()
        self.assertEqual(1, self.number_of_test_runs)

    def test_runs_tests_when_change_detected(self):
        fake_monitor = self.FakeMonitor(look_for_changes_returns = [True])
        pytddmon = Pytddmon(self.fake_filefinder, fake_monitor)
        pytddmon.main()
        self.assertEqual(2, self.number_of_test_runs)

    def test_doesnt_run_tests_when_no_change(self):
        fake_monitor = self.FakeMonitor(look_for_changes_returns = [True, False])
        pytddmon = Pytddmon(self.fake_filefinder, fake_monitor)
        pytddmon.main()
        pytddmon.main()
        self.assertEqual(2, self.number_of_test_runs)

    def test_runs_each_time_a_change_is_detected(self):
        runs = 10
        fake_monitor = self.FakeMonitor(look_for_changes_returns = [True]*runs)
        pytddmon = Pytddmon(self.fake_filefinder, fake_monitor)
        for _ in range(runs):
            pytddmon.main()
        self.assertEqual(runs + 1, self.number_of_test_runs)

if __name__ == '__main__':
    unittest.main()
