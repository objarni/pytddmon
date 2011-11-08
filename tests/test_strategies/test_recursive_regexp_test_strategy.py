import unittest
import os.path
from pytddmon import RecursiveRegexpTestStartegy


class RememberTestRunner(object):
    def __init__(self):
        self.roots = []
        self.file_paths = []
    def __call__(self, arguments):
        root, file_path = arguments
        self.roots.append(root)
        self.file_paths.append(file_path)
        return (0,0,"")


class StaticTestRunner(object):
    def __init__(self, things):
        self.things = things
        self.iter = iter(self.things)
    def __call__(self,argument):
        try:
            return self.iter.next()
        except:
            self.iter = iter(self.thing)
            return self.iter.next()
        

class RecursiveRegexpTestStrategyTestCase(unittest.TestCase):

    def test_run_tests_in_all_files(self):
        test_files = ["test_file.py", "test_other.py"]
        data_files = ["data.dat", "image.jpg"]
        all_files = test_files + data_files
        rtr = RememberTestRunner()
        rrts = RecursiveRegexpTestStartegy(
            root="/",
            expr="test_.*\\.py",
            test_runner=rtr,
            walker=lambda root:((root, [], all_files) for n in [None])
        )
        rrts.run_tests([], pool=False)
        file_names = map(os.path.basename, rtr.file_paths)
        sorted_file_names = sorted(file_names)
        sorted_test_files = sorted(test_files)
        assert sorted_file_names == sorted_test_files ,"%r!=%r" % (
            sorted_file_names,
            sorted_test_files
        ) 

    def test_return_value(self):
        test_files = ["test_file.py", "test_other.py"]
        data_files = ["data.dat", "image.jpg"]
        all_files = test_files + data_files
        strunner = StaticTestRunner(
            [
                (1, 1, ""),
                (2,2, "")
            ]
        )
        rrts = RecursiveRegexpTestStartegy(
            root="/",
            expr="test_.*\\.py",
            test_runner=strunner,
            walker=lambda root:((root, [], all_files) for n in [None])
        )
        green, totals, log = rrts.run_tests([], pool=False)
        assert green==3 and totals==3, "greens=%r, totals=%r" % (
            green,
            total
        )

