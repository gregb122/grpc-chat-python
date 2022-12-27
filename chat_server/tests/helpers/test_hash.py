import unittest
import logging

from ...src.helpers.hash import Hash

class TestUserAuth(unittest.TestCase):
    
    def test_bcrypt(self):
        res = Hash.bcrypt("123456789xD")
        self.assertIsInstance(res, str)
        self.assertTrue(res)
    
    def test_verify(self):
        res = Hash.bcrypt("123456789xD")
        self.assertTrue(
            Hash.verify(res, "123456789xD"))

if __name__ == '__main__':
    unittest.main()