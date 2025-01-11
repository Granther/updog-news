import unittest

from app.infer import Infer

class TestInfer(unittest.TestCase):
    def test_gen(self):
        infer = Infer()
        self.assertTrue(infer._gen("How are you", "You are a helpful AI", "feather"))