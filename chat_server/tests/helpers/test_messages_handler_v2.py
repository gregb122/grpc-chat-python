import unittest
from unittest.mock import Mock, patch, call

import etcd

from chat_server.src.helpers.messages_handler_v2 import EtcdMessagesHandler


class UserAuthTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.client = Mock()    
        self.MessagesHandler = EtcdMessagesHandler(self.client, 
                                                   "user")
        self._to_send_str = f"/users/user/to_send_queue"
        self._sent_str = f"/users/user/sent_queue"

    def test_init(self):
        """Tests chat_server.src.helpers.messages_handler_v2.__init__() method."""
        read_mock = Mock()        
        write_mock = Mock()
        _client = Mock(read=read_mock, write=write_mock)

        EtcdMessagesHandler.__init__(Mock(), _client, "user")
        read_mock.assert_called_once()
        write_mock.call_count = 2

    def test_init_etcd_key_not_found(self):
        """Tests chat_server.src.helpers.messages_handler_v2.__init__() method."""
        read_mock = Mock(
            side_effect=etcd.EtcdKeyNotFound(
                message="Peace is a lie",
                payload="There is only passion",
            )
        )
        
        _client = Mock(read=read_mock)

        with self.assertRaises(KeyError) as context:
            EtcdMessagesHandler.__init__(Mock(), _client, "nonexistetd_user")
        self.assertIn("User not found", str(context.exception))

    @patch("chat_server.src.helpers.messages_handler_v2.logging")
    def test_init_etcd_already_exist(self, _logging: Mock):
        """Tests chat_server.src.messages_handler_v2.__init__() method."""
        read_mock = Mock()
        write_mock = Mock(
            side_effect=etcd.EtcdAlreadyExist(
                message="Peace is a lie",
                payload="There is only passion",
            )
        )
        _client = Mock(read=read_mock, write=write_mock)

        EtcdMessagesHandler.__init__(Mock(), _client, "user")
        read_mock.assert_called_once()
        write_mock.call_count = 2
        _logging.info.call_count = 2

    def test_add_message_to_queue_to_send(self):
        _write = Mock()
        self.client.write = _write
        
        self.MessagesHandler.add_message_to_queue(True, "Message")
        
        _write.assert_called_once_with(
            self._to_send_str,
            "Message",
            append=True,
        )

    def test_add_message_to_queue_sent(self):
        _write = Mock()
        self.client.write = _write
        
        self.MessagesHandler.add_message_to_queue(False, "Message")
        
        _write.assert_called_once_with(
            self._sent_str,
            "Message",
            append=True,
        )
    
    def test_get_elems_from_queue_to_send(self):
        """Tests chat_server.src.helpers.messages_handler_v2.login_user() method."""
        _read = Mock(
            return_value=Mock(
                leaves=iter([Mock(key="000", value="Message0"), 
                        Mock(key="001", value="Message1")])
            )
        )
        self.client.read = _read
        
        self.assertListEqual(
            self.MessagesHandler.get_elems_from_queue(True),
            [("000", "Message0")]
        )
        
        _read.assert_called_once_with(
                self._to_send_str,
                recursive=True,
                wait=False,
                sorted=True,
                timeout=None,
        )

    def test_get_elems_from_queue_sent(self):
        """Tests chat_server.src.helpers.messages_handler_v2.login_user() method."""
        _read = Mock(
            return_value=Mock(
                leaves=iter([Mock(key="000", value="Message0"), 
                        Mock(key="001", value="Message1")])
            )
        )
        self.client.read = _read
        
        self.assertListEqual(
            self.MessagesHandler.get_elems_from_queue(False),
            [("000", "Message0")]
        )
        
        _read.assert_called_once_with(
                self._sent_str,
                recursive=True,
                wait=False,
                sorted=True,
                timeout=None,
        )
        
    def test_get_all_elems_from_queue_to_send(self):
        """Tests chat_server.src.helpers.messages_handler_v2.login_user() method."""
        _read = Mock(
            return_value=Mock(
                leaves=iter([
                    Mock(key="000", value="Message0"), 
                    Mock(key="001", value="Message1")
                ])
            )
        )
        self.client.read = _read
        
        self.assertListEqual(
            self.MessagesHandler.get_elems_from_queue(True, get_all=True),
            [("000", "Message0"), ("001", "Message1")]
        )
        
        _read.assert_called_once_with(
                self._to_send_str,
                recursive=True,
                wait=False,
                sorted=True,
                timeout=None,
        )

    def test_get_elems_from_queue_to_send_exception(self):
        """Tests chat_server.src.helpers.messages_handler_v2.login_user() method."""
        _read = Mock(
            side_effect=Exception()
        )
        self.client.read = _read

        self.assertListEqual(
            self.MessagesHandler.get_elems_from_queue(True),
            []
        )

    def test_store_and_delete_sent_message(self):
        """Tests chat_server.src.helpers.messages_handler_v2.login_user() method."""
        _write = Mock()
        self.client.write = _write
        
        _delete = Mock()
        self.client.delete = _delete
        
        self.MessagesHandler.store_and_delete_sent_message("000", "Message"),

        
        _write.assert_called_once_with(
                self._sent_str, 
                "Message", 
                append=True
        )
        _delete.assert_called_once_with("000")
        
    def test_store_and_delete_sent_messages(self):
        """Tests chat_server.src.messages_handler_v2.login_user() method."""
        self.MessagesHandler.test_store_and_delete_sent_message = Mock()
        
        
        self.MessagesHandler.store_and_delete_sent_messages(
            [("000", "Message0"), ("001", "Message1")]
        )
        
        self.MessagesHandler.test_store_and_delete_sent_message.call_count = 2
        
        
if __name__ == '__main__':
    unittest.main()