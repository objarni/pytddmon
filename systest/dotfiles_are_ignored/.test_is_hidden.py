# This file will be ignored by pytddmon since it's begins with a ".",
# which per UNIX conventions means it is to be treated as hidden.
# This is necessary e.g. since emacs creates dotfiles when saving,
# in same directory as unit test.

import unittest

class TestClass(unittest.TestCase):
    def test1(self):
        assert True

