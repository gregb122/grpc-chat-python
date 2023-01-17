import unittest
from unittest.mock import Mock

from chat_server.src.helpers.hash import Hash

class TestUserAuth(unittest.TestCase):
    
    def test_bcrypt(self):
        Hash.pwd_ctx = Mock(
            hash=Mock(
                return_value="hashed"
            )
        )
        res = Hash.bcrypt("plain")
        self.assertEqual(res, "hashed")
        Hash.pwd_ctx.hash.assert_called_once()
    
    def test_verify(self):
        Hash.pwd_ctx = Mock(
            verify=Mock(
                return_value=True
            )
        )
        res = Hash.verify("hashed", "plain")
        self.assertTrue(res)
        Hash.pwd_ctx.verify.assert_called_once()
if __name__ == '__main__':
    unittest.main()