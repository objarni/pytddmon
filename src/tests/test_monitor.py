# coding: utf-8
import unittest
from pytddmon import Monitor


class TestChangeDetection(unittest.TestCase):

    def _set_up_monitor(self):
        files = ['file']
        file_finder = lambda: files
        get_file_size = lambda x: 1
        get_file_modification_time = lambda x: 1
        monitor = Monitor(file_finder, get_file_size, get_file_modification_time)
        return files, monitor

    def test_modification_time_changed(self):
        files = ['file']
        file_finder = lambda: files
        get_file_size = lambda x: 1

        modtime = [1]
        get_file_modification_time = lambda x: modtime[0]

        monitor = Monitor(file_finder, get_file_size, get_file_modification_time)
        modtime[0] = 2
        change_detected = monitor.look_for_changes()
        assert change_detected

    def test_nothing_changed(self):
        files, monitor = self._set_up_monitor()
        change_detected = monitor.look_for_changes()
        assert not change_detected

    def test_adding_file(self):
        files, monitor = self._set_up_monitor()
        files.append('file2')
        change_detected = monitor.look_for_changes()
        assert change_detected

    def test_renaming_file(self):
        files, monitor = self._set_up_monitor()
        files[0] = 'renamed'
        change_detected = monitor.look_for_changes()
        assert change_detected

    def test_change_is_only_detected_once(self):
        files, monitor = self._set_up_monitor()
        files[0] = 'changed'
        change_detected = monitor.look_for_changes()
        change_detected = monitor.look_for_changes()
        assert not change_detected

    def test_file_size_changed(self):
        files = ['file']
        filesize = [1]
        file_finder = lambda: files
        get_file_size = lambda x: filesize[0]
        get_file_modification_time = lambda x: 1

        monitor = Monitor(file_finder, get_file_size, get_file_modification_time)
        filesize[0] = 5
        change_detected = monitor.look_for_changes()
        assert change_detected

    def test_file_order_does_not_matter(self):
        files = ['file', 'file2']
        file_finder = lambda: files
        get_file_size = lambda x: 1
        get_file_modification_time = lambda x: 1

        monitor = Monitor(file_finder, get_file_size, get_file_modification_time)
        files[:] = ['file2', 'file']
        change_detected = monitor.look_for_changes()
        assert not change_detected

if __name__ == '__main__':
    unittest.main()
