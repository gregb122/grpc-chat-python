import unittest

from unittest.mock import Mock, patch, call

from chat_server.src.main import ChatServer

class TestServerCalls(unittest.TestCase):
    @patch("chat_server.src.main.etcd")
    def setUp(self, etcd: Mock) -> None:
        self.etcd_client = Mock()
        etcd.Client.return_value = self.etcd_client 
        self.chat_server = ChatServer()

    @patch("chat_server.src.main.etcd")
    def test_init(self, _etcd: Mock):
        """Tests chat_server.src.auth.__init__() method."""

        ChatServer.__init__(Mock())
        _etcd.Client.assert_called_once_with(
            host="172.28.0.2",
            port=2379,
            protocol="http"
        )

    @patch("chat_server.src.main.chat_pb2")
    @patch("chat_server.src.main.UserAuth")
    @patch("chat_server.src.main.logging")
    def test_get_all_users(self, _logging: Mock, user_auth: Mock, chat_pb2: Mock):
        """Tests chat_server.src.auth.login_user() method."""
        user_auth.list_registered_users.return_value = []
        user_auth.return_value = user_auth

        self.chat_server.GetAllUsers(Mock(), Mock())

        _logging.info.assert_called_once_with("List all registred users: ")
        user_auth.assert_called_once()
        user_auth.list_registered_users.assert_called_once()

    @patch("chat_server.src.main.chat_pb2")
    @patch("chat_server.src.main.EtcdMessagesHandler")
    @patch("chat_server.src.main.logging")
    @patch("chat_server.src.main.MessageToJson")
    def test_send_message(self,
                          message_to_json: Mock, 
                          _logging: Mock, 
                          etcd_message_handler: Mock, 
                          chat_pb2: Mock):
        """Tests chat_server.src.auth.login_user() method."""
        request = Mock(
            message=Mock(
                to_user_login="Batman",
                from_user_login="Joker",
            )
        )
        send_handler, store_handler = Mock(), Mock()
        etcd_message_handler.side_effect = [send_handler, store_handler]
        message_to_json.return_value = ""
        
        self.chat_server.SendMessage(request, Mock())
        
        etcd_message_handler.assert_has_calls([
            call(
                client=self.etcd_client,
                to_user="Batman",
            ),
            call(
                client=self.etcd_client,
                to_user="Joker",
            ),
        ])
        send_handler.add_message_to_queue.assert_called_once_with(
            to_send_queue=True,
            value=""
        )
        store_handler.add_message_to_queue.assert_called_once_with(
            to_send_queue=False,
            value=""
        )
        _logging.debug.assert_called_once()
        chat_pb2.SendMessageReply.assert_called_once()

    @patch("chat_server.src.main.EtcdMessagesHandler")
    @patch("chat_server.src.main.grpc")
    def test_send_message_user_not_found(self,
                                         grpc: Mock,
                                         etcd_message_handler: Mock):
        """Tests chat_server.src.main.SendMessage() method (User not found)."""
        request = Mock(
            message=Mock(
                to_user_login="Bruce",
            )
        )
        etcd_message_handler.side_effect=KeyError()
        context = Mock(
            abort=Mock()
        )
          
        self.chat_server.SendMessage(request, context)
        
        context.abort.assert_called_once_with(
            grpc.StatusCode.NOT_FOUND, 
            f"User Bruce not found"
        )

if __name__ == '__main__':
    unittest.main()