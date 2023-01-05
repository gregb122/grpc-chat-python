import unittest

from unittest.mock import Mock, patch, call

from chat_server.src.main import ChatServer

# class TestServerCalls(unittest.TestCase):
#     def setUp(self) -> None:
#         pass
    
#     def __init__(self, methodName) -> None:
#         pass
#         # super().__init__(methodName)
        
#         # myServicer = ChatServer()
#         # servicers = {
#         #     chat_pb2.DESCRIPTOR.services_by_name['ChatService']: myServicer
#         # }
#         # self.test_server = server_from_dictionary(
#         #     servicers, strict_real_time())

#     def test_get_all_users(self):
#         pass

# if __name__ == '__main__':
#     unittest.main()