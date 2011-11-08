import unittest

from pytddmon import DefaultHasher

class FakeOsModule(object):
    def __init__(self, stats):
        self.stats = iter(stats)
        self.st_size = 0
        self.st_mtime = 0

    def stat(self, file_path):
        self.st_size, self.st_mtime = self.stats.next()
        return self

class FakeErrorOsModule(object):
    def stat(self, file_path):
        raise IOError(
            "OSError: [Errno 2] No such file or directory: '%s'" %
            file_path
        )

class DefaultHasherTester(unittest.TestCase):

    def test_sum_of_size_and_mtime_are_constant_but_differrent(self):
        os_module = FakeOsModule([(3,1),(2,2)])
        hasher = DefaultHasher(os_module)
        a = hasher("")
        b = hasher("") 
        assert a != b, "%d, %d"%(a, b)

    def test_when_size_and_mtime_switches_place(self):
        os_module = FakeOsModule([(2,1),(1,2)])
        hasher = DefaultHasher(os_module)
        a = hasher("")
        b = hasher("")
        assert a != b, "%r, %r"%(a, b)

    def test_when_file_dont_exist(self):
        os_module = FakeErrorOsModule()
        hasher = DefaultHasher(os_module)
        with self.assertRaises(IOError):
            hasher("")
        
        
        
