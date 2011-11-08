import unittest
import os
from pytddmon import RecursiveRegexpFileStartegy

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

class RecursiveRegexpFileStartegyTest(unittest.TestCase):

    def test_empty_project(self):
        hasher = FakeHasher()
        rrfs = RecursiveRegexpFileStartegy(
            root=".",
            expr="test_.*\\.py",
            walker=lambda root:((root,[],[]) for n in [1]),
            hasher=hasher
        )
        assert rrfs.which_files_has_changed() == []

    def test_project_with_one_file(self):
        hasher = FakeHasher()
        rrfs = RecursiveRegexpFileStartegy(
            root="/",
            expr=".*\\.py",
            walker=lambda root:((root,[],["file.py"]) for n in [1]),
            hasher=hasher
        )
        assert ["/file.py"] == rrfs.which_files_has_changed()

    def test_project_with_two_files_one_match_expr(self):
        hasher = FakeHasher()
        rrfs = RecursiveRegexpFileStartegy(
            root="/",
            expr=".*\\.py",
            walker=lambda root:((root,[],["data.dat","file.py"]) for n in [1]),
            hasher=hasher
        )
        assert ["/file.py"] == rrfs.which_files_has_changed()
        
    def tests_project_with_one_file_in_folder(self):
        hasher = FakeHasher()
        rrfs = RecursiveRegexpFileStartegy(
            root="/",
            expr=".*\\.py",
            walker=lambda root:(
                t for t in [
                    (root, ["folder"], []),
                    (os.path.join(root, "folder"), [], ["file.py"])
                ]
            ),
            hasher=hasher
        )
        assert [os.path.join("/","folder","file.py")] == rrfs.which_files_has_changed()
