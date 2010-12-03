import unittest
from pyTDDmon import calculate_checksum

class FakeFileInfo:
  def get_size(self, path):
    return self.fake_size
  def get_modified_time(self, path):
    return self.fake_time

class test_calculate_checksum(unittest.TestCase):
	def setUp(self):
		self.fileinfo_fake = FakeFileInfo()
		self.fileinfo_fake.fake_size = 1
		self.fileinfo_fake.fake_time = 2
		self.val1 = calculate_checksum(["somefile.py"], self.fileinfo_fake)
		
	def tearDown(self):
		val2 = calculate_checksum(["somefile.py"], self.fileinfo_fake)
		change_detected = val2 != self.val1
		assert change_detected
		
	def test_modified_time_changed(self):
		self.fileinfo_fake.fake_time = 3
		
	def test_size_changed(self):
		self.fileinfo_fake.fake_size = 3

