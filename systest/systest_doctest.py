import unittest
import util

class TestCase(unittest.TestCase):
    def test_that_no_tests_are_found(self):
        gui_data = util.run_pytddmon_in_test_mode()
        self.assertEqual(gui_data['green'], '0')
        self.assertEqual(gui_data['total'], '0')

if __name__ == '__main__':
    unittest.main(verbosity=0)