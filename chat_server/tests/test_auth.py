import unittest
from unittest.mock import Mock, patch, call

import etcd

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

    @patch("chat_server.src.auth.Hash")
    @patch("chat_server.src.auth.logging")
    @patch("chat_server.src.auth.MessageToJson")
    @patch("chat_server.src.auth.Timestamp")
    @patch("chat_server.src.auth.chat_pb2")
    def test_register_user(self,
                           chat_pb2: Mock,
                           timestamp: Mock, 
                           messageToJson: Mock, 
                           _logging: Mock,
                           hash: Mock):
        """Tests chat_server.src.auth.register_user() method."""
        _write = Mock()
        self.client.write = _write
        
        user_info = Mock(login="Darth Vitiate")
        register_user_rquest = Mock(
            user_info=user_info, 
            password="Darth Nox"
        )
        
        chat_pb2.UserInfo.return_value = Mock()
        chat_pb2.EtcdUserInfo.return_value = Mock()
        
        messageToJson.return_value = "Converted to json"
        timestamp.ToJsonString.return_value = "some_json_date"
        hash.bcrypt.return_value = "Darth Nox Hashed"

        self.auth.register_user(register_user_rquest)
        
        timestamp.assert_called_once()
        messageToJson.assert_called_once()
        # chat_pb2.EtcdUserInfo.assert_called_with(
        #     user_info=chat_pb2.UserInfo.return_value,
        #     is_active=True,
        #     hashed_password=hash.bcrypt.return_value,
        #     register_timestamp=timestamp.ToJsonString.return_value
        # )
        
        self.client.write.assert_called_with(
            f"/users/Darth Vitiate/user_info",
            messageToJson.return_value,
            prevExist=False
            )
        hash.bcrypt.assert_called_once_with(
            "Darth Nox",
        )
        _logging.info.assert_called_once()

    def test_register_user_etcd_already_exist(self):
        """Tests chat_server.src.auth.register_user() method (EtcdAlreadyExist)."""
        _write = Mock(
            side_effect=etcd.EtcdAlreadyExist(
                message="Peace is a lie",
                payload="There is only passion",
            )
        )
        self.client.write = _write
        
        user_info = Mock(login="Darth Baras")
        register_user_rquest = Mock(
            user_info=user_info
        )
        
        with self.assertRaises(KeyError) as context:
            self.auth.register_user(register_user_rquest)
        self.assertIn("User Darth Baras already registered", str(context.exception))

    @patch("chat_server.src.auth.logging")
    @patch("chat_server.src.auth.Parse")
    @patch("chat_server.src.auth.chat_pb2")
    def test_list_registered_users(self, 
                                   chat_pb2: Mock, 
                                   parse: Mock, 
                                   _logging: Mock):
        
        _etcd_read_users_response = Mock(
            leaves=[Mock(key="user0"), Mock(key="user1")]
        )
        _etcd_read_user_info_response = Mock(
            value=Mock()
        )
        _read = Mock(
            side_effect=[_etcd_read_users_response, 
                         _etcd_read_user_info_response,
                         _etcd_read_user_info_response]
        )
        self.client.read = _read
        chat_pb2.EtcdUserInfo.return_value = Mock()
        _user_info = Mock(user_info=Mock())
             
        parse.return_value = _user_info
        self.assertListEqual(
            self.auth.list_registered_users(),
            [_user_info.user_info, _user_info.user_info]
        )
        
        self.client.read.assert_has_calls([
            call(f"/users", sorted=True),
            call(f"user0/user_info"),
            call(f"user1/user_info")
        ])
        _user_info.user_info.call_count = 2
        _logging.info.call_count = 2
        chat_pb2.EtcdUserInfo.call_count = 2


if __name__ == '__main__':
    unittest.main()