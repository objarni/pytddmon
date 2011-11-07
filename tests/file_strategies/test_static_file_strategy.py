import unittest
from pytddmon import StaticFileStartegy

class FakeHasher(object):
    def __init__(self):
        self.file_paths = {}
    def __call__(self, file_path):
        return self.file_paths.get(file_path, 0)
    def change_file(self, file_path):
        self.file_paths[file_path] = self.file_paths.get(file_path, 0) + 1
class FakeErrorHasher(object):
    def __call__(self, path):
        raise IOError(
            "OSError: [Errno 2] No such file or directory: '%s'" %
            path
        )
        

class StaticFileStartegyTest(unittest.TestCase):

    def test_firstrun(self):
        hasher = FakeHasher()
        all_files = ["/file1.py", "/data1.dat"]
        sfs = StaticFileStartegy(all_files, hasher=hasher)
        assert sfs.which_files_has_changed() == all_files

    def test_one_file_change_of_two(self):
        hasher = FakeHasher()
        all_files = ["/file1.py", "/data1.dat"]
        sfs = StaticFileStartegy(all_files, hasher=hasher)
        sfs.which_files_has_changed()
        hasher.change_file("/data1.dat")
        assert sfs.which_files_has_changed() == ["/data1.dat"]
    
    def test_look_file_thet_dont_exists(self):
        hasher = FakeErrorHasher()
        all_files = ["/file1.py", "/data1.dat"]
        sfs = StaticFileStartegy(all_files, hasher=hasher)
        assert [] == sfs.which_files_has_changed()
        
        
        
