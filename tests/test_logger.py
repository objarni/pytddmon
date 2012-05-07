import unittest
from pytddmon import DefaultLogger

class TestOrder(unittest.TestCase):
    def setUp(self):
        self.messages = [
            "hello!",
            "world!",
            "pytddmon!",
        ]
        self.logger = DefaultLogger()

    def expected(self, levels):
        return "\n".join(
            "[%s]%s" %(
                level,
                message
            )
            for message, level in zip(self.messages, levels)
        )
    def test_3_of_same_level(self):
        for message in self.messages:
            self.logger.log(message)
        log = self.logger.getlog() 
        expected = self.expected(["all"] * 3)
        assert log == expected, "%r!=%r" % (log, expected)

    def test_3_of_different_level(self):
        levels = [
            "info",
            "warning",
            "info"
        ]
        for message, level in zip(self.messages, levels):
            self.logger.log(message, level)
        log = self.logger.getlog() 
        expected = self.expected(levels)
        assert log == expected, "%r!=%r" % (log, expected)
