import unittest
import os.path
from pytddmon import StaticTestStrategy
from pytddmon import ON_PYTHON3
from pytddmon import DefaultLogger


class FakeHasher(object):
    def __init__(self):
        self.file_paths = {}
    def __call__(self, file_path):
        return self.file_paths.get(file_path, 0)
    def change_file(self, file_path):
        self.file_paths[file_path] = self.file_paths.get(file_path, 0) + 1

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
        if ON_PYTHON3:
            try:
                return self.iter.__next__()
            except:
                self.iter = iter(self.thing)
                return self.iter.__next__()
        else:
            try:
                return self.iter.next()
            except:
                self.iter = iter(self.thing)
                return self.iter.next()
        

class StaticTestStrategyTestCase(unittest.TestCase):

    def test_run_tests_in_all_files(self):
        files = ["test.py", "other.py"]
        rtr = RememberTestRunner()
        sts = StaticTestStrategy(
            files,
            test_runner=rtr,
            hasher=FakeHasher()
        )
        sts.run_tests([], DefaultLogger(), pool=False)
        file_names = map(os.path.basename, rtr.file_paths)
        assert sorted(file_names) == sorted(files)

    def test_correct_return(self):
        files = ["test.py", "other.py"]
        strunner = StaticTestRunner(
            [
                (1,1,""),
                (1,1,"")
            ]
        )
        sts = StaticTestStrategy(
            files,
            test_runner=strunner,
            hasher=FakeHasher()
        )
        greens, total = sts.run_tests([], DefaultLogger(), pool=False)
        assert greens==2 and total == 2
        
        
