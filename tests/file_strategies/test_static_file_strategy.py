import unittest
import os
from pytddmon import StaticFileStartegy
from tests.fakes import FakeHasher
from tests.fakes import FakeErrorHasher

class StaticFileStartegyTest(unittest.TestCase):

    def test_firstrun(self):
        hasher = FakeHasher()
        all_files = sorted(
            ["/file1.py", "/data1.dat"]
        )
        all_files = [
            os.path.abspath(file_path)
            for file_path in all_files
        ]
        sfs = StaticFileStartegy(all_files, hasher=hasher)
        out = sorted(
            sfs.which_files_has_changed() 
        )
        assert out == all_files, "%r!=%r" %(
            out,
            all_files
        )

    def test_one_file_change_of_two(self):
        hasher = FakeHasher()
        all_files = ["/file1.py", "/data1.dat"]
        all_files = [
            os.path.abspath(file_path)
            for file_path in all_files
        ]
        sfs = StaticFileStartegy(all_files, hasher=hasher)
        sfs.which_files_has_changed()
        hasher.change_file(all_files[-1])
        assert sfs.which_files_has_changed() == all_files[-1:]
    
    def test_look_file_thet_dont_exists(self):
        hasher = FakeErrorHasher()
        all_files = ["/file1.py", "/data1.dat"]
        sfs = StaticFileStartegy(all_files, hasher=hasher)
        assert [] == sfs.which_files_has_changed()
        
        
        
