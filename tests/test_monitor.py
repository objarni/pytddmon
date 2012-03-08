# coding: utf-8
import unittest
from pytddmon import Monitor

class test_change_detection(unittest.TestCase):

    def test_modification_time_changed(self):
        def file_finder():
            return ['file']
        def get_file_size(file):
            return 1
        modtime = [1]
        def get_file_modification_time(file):
            return modtime[0]
        monitor = Monitor(file_finder, get_file_size, get_file_modification_time)
        modtime[0] = 2
        change_detected = monitor.look_for_changes()
        assert change_detected

    def test_nothing_changed(self):
        def file_finder():
            return ['file']
        def get_file_size(file):
            return 1
        def get_file_modification_time(file):
            return 1
        monitor = Monitor(file_finder, get_file_size, get_file_modification_time)
        change_detected = monitor.look_for_changes()
        assert not change_detected

    def test_adding_file(self):
        files = ['file']
        def file_finder():
            return files
        def get_file_size(file):
            return 1
        def get_file_modification_time(file):
            return 1
        monitor = Monitor(file_finder, get_file_size, get_file_modification_time)
        files.append('file2')
        change_detected = monitor.look_for_changes()
        assert change_detected

    def test_renaming_file(self):
        files = ['file']
        def file_finder():
            return files
        def get_file_size(file):
            return 1
        def get_file_modification_time(file):
            return 1
        monitor = Monitor(file_finder, get_file_size, get_file_modification_time)
        files[0] = 'renamed'
        change_detected = monitor.look_for_changes()
        assert change_detected

    def test_change_is_only_detected_once(self):
        files = ['file']
        def file_finder():
            return files
        def get_file_size(file):
            return 1
        def get_file_modification_time(file):
            return 1
        monitor = Monitor(file_finder, get_file_size, get_file_modification_time)
        files[0] = 'changed'
        change_detected = monitor.look_for_changes()
        change_detected = monitor.look_for_changes()
        assert not change_detected

    def test_file_size_changed(self):
        files = ['file']
        filesize = [1]
        def file_finder():
            return files
        def get_file_size(file):
            return filesize[0]
        def get_file_modification_time(file):
            return 1
        monitor = Monitor(file_finder, get_file_size, get_file_modification_time)
        filesize[0] = 5
        change_detected = monitor.look_for_changes()
        assert change_detected

if __name__ == '__main__':
    unittest.main()
