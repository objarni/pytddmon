import unittest
from collections import namedtuple
from pytddmon import Pytddmon

class FakeTestStrategy(object):
    def __init__(self):
        self.run = False
        self.files = []
    def run_tests(self, filepaths=None):
        self.run = True
        self.files = filepaths
        return (0, 0, "")

class PytddmonTestCase(unittest.TestCase):
    def test_which_files_hash_changed(self):
        files = ["file1", "file2"]
        pytddmon = Pytddmon(
            file_strategies=[
                namedtuple("FileStrategy",["which_files_has_changed"])(
                lambda:files
                )
            ]
        )
        assert pytddmon.which_files_has_changed() == files
    def test_run_tests(self):
        fts = FakeTestStrategy()
        pytddmon = Pytddmon(
            test_strategies=[
                fts
            ]
        )
        pytddmon.run_tests()
        assert fts.run
    def test_main(self):
        files = ["file1", "file2"]
        fts = FakeTestStrategy()
        pytddmon = Pytddmon(
            test_strategies=[
                fts
            ],
            file_strategies=[
                namedtuple("FileStrategy",["which_files_has_changed"])(
                lambda:files
                )
            ]
        )
        pytddmon.main()
        assert fts.run
        assert files == fts.files

        
        
