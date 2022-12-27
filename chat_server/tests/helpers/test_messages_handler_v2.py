import unittest

from unittest.mock import Mock, patch

from ...src.helpers.messages_handler_v2 import EtcdMessagesHandler
from common import chat_pb2

class TestMessagesHandler(unittest.TestCase):
    def setUp(self) -> None:
            self._client = Mock(
            write=Mock(
                return_value=None,
                side_effect=[]
                # WaitOptions=Mock(
                #     return_value=opts,
                # )
            )

        )
    
    def test_init(self):
        """Test make_verify_param method."""

        config = {
            
            "ca_bundle_file": "ca_bundle_file"
        }
        result = EtcdMessagesHandler(config)
        
    
    def test_add_message_to_queue(self):
        pass


if __name__ == '__main__':
    unittest.main()