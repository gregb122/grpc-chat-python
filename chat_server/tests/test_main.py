import unittest

from grpc import StatusCode
from grpc_testing import server_from_dictionary, strict_real_time
from ..src import main
from common import chat_pb2

class TestServerCalls(unittest.TestCase):
    # Q: How can i mock ETCD here? Or it should be used only for functional tests?

    def __init__(self, methodName) -> None:
        super().__init__(methodName)
        
        myServicer = main.ChatServer()
        servicers = {
            chat_pb2.DESCRIPTOR.services_by_name['ChatService']: myServicer
        }
        self.test_server = server_from_dictionary(
            servicers, strict_real_time())

    def test_get_all_users(self):
        request = chat_pb2.GetAllUsersRequest(
        )
        method = self.test_server.invoke_unary_unary(
            method_descriptor=(chat_pb2.DESCRIPTOR
                .services_by_name['ChatService']
                .methods_by_name['GetAllUsers']),
            invocation_metadata={},
            request=request, timeout=1)

        response, metadata, code, details = method.termination()
        self.assertTrue(bool(response.users == []))
        self.assertEqual(code, StatusCode.OK)

if __name__ == '__main__':
    unittest.main()