import unittest
from unittest.mock import Mock, patch

import etcd

from common import chat_pb2
from chat_server.src.auth import UserAuth


class UserAuthTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.client = Mock()    
        self.auth = UserAuth(self.client)

    def test_init(self):
        """Tests chat_server.src.auth.__init__() method."""
        write_mock = Mock()
        _client = Mock(write=write_mock)

        UserAuth.__init__(Mock(), _client)
        write_mock.assert_called_once()

    @patch("chat_server.src.auth.Hash")
    @patch("chat_server.src.auth.logging")
    @patch("chat_server.src.auth.Parse")
    def test_login_user(self, parse: Mock, _logging: Mock,
                        hash: Mock):
        """Tests chat_server.src.auth.login_user() method."""
        _read = Mock()
        self.client.read = _read

        parsed_etcd_user = Mock(hashed_password="Darth Angral")
        parse.return_value = parsed_etcd_user
        user = Mock(
            user="Darth Vitiate",
            password="Darth Nox",
        )

        hash.verify.return_value = True

        self.auth.login_user(user)
        parse.assert_called_once()
        hash.verify.assert_called_once_with(
            hashed_password="Darth Angral",
            plain_password="Darth Nox",
        )
        _logging.info.assert_called_once()

    def test_login_user_etcd_not_found(self):
        """Tests chat_server.src.auth.login_user() method (EtcdKeyNotFound)."""
        _read = Mock(
            side_effect=etcd.EtcdKeyNotFound(
                message="Peace is a lie",
                payload="There is only passion",
            )
        )
        self.client.read = _read

        user = Mock(login="Darth Baras")

        with self.assertRaises(KeyError) as context:
            self.auth.login_user(user)
        self.assertIn("Login Darth Baras failed", str(context.exception))


if __name__ == '__main__':
    unittest.main()
