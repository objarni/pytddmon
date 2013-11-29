# coding: utf-8
""""
#- kör tester från början
#- kör inte tester om ingen förändring
#- kör tester om förändring
- summa finns i .total_tests
- gröna finns i .total_passed_tests
"""

import sys
sys.path.append('..')

import unittest
from pytddmon import Pytddmon


class TestPytddmonMonitorCommunication(unittest.TestCase):
    class FakeMonitor:
        def __init__(self, look_for_changes_returns):
            self.returns = list(look_for_changes_returns)
            self.returns.reverse()

        def look_for_changes(self):
            return self.returns.pop()

    def setUp(self):
        self.number_of_test_runs = 0

    def _set_up_pytddmon(self, params):
        fake_monitor = self.FakeMonitor(look_for_changes_returns=params)
        pytddmon = Pytddmon(self.fake_filefinder, fake_monitor)
        pytddmon.main()
        return pytddmon

    def fake_filefinder(self):
        self.number_of_test_runs += 1
        return []

    def test_runs_tests_at_boot(self):
        self._set_up_pytddmon([False])
        self.assertEqual(1, self.number_of_test_runs)

    def test_runs_tests_when_change_detected(self):
        self._set_up_pytddmon([True])
        self.assertEqual(2, self.number_of_test_runs)

    def test_doesnt_run_tests_when_no_change(self):
        pytddmon = self._set_up_pytddmon([True, False])
        pytddmon.main()
        self.assertEqual(2, self.number_of_test_runs)

    def test_runs_each_time_a_change_is_detected(self):
        runs = 10
        fake_monitor = self.FakeMonitor(look_for_changes_returns=([True] * runs))
        pytddmon = Pytddmon(self.fake_filefinder, fake_monitor)
        for _ in range(runs):
            pytddmon.main()
        self.assertEqual(runs + 1, self.number_of_test_runs)

    def test_total_tests_is_zero_if_no_tests_are_run(self):
        pytddmon = self._set_up_pytddmon([False])
        self.assertEqual(0, pytddmon.total_tests_run)

if __name__ == '__main__':
    unittest.main()
