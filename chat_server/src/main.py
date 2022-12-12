import logging
from concurrent import futures
from typing import Dict, List

import etcd
import grpc
import protobufs.chat_pb2 as chat_pb2
import protobufs.chat_pb2_grpc as chat_pb2_grpc
from google.protobuf.json_format import MessageToJson, Parse
from auth import UserAuth
from helpers.messages_handler_v2 import EtcdMessagesHandler


class ChatServer(chat_pb2_grpc.ChatServiceServicer):
    """A class to represent a server object.

    Args:
        chat_pb2_grpc: Protobuf grpc auto generated class.
    """
    def __init__(self) -> None:
        """Constructs chat server object, connect and gets client ETCD object.
        """
        self.etcd_client = etcd.Client(host="172.28.0.2", port=2379, protocol="http")


    def GetAllUsers(self, request, context) -> chat_pb2.GetAllUsersReply:
        """Gets registred users.

        Args:
            request: Request defined in chat.proto file.
            context: grpc context.

        Returns:
            chat_pb2.GetAllUsersReply: Reply defined in chat.proto file.
        """
        logging.info("List all registred users")
        return chat_pb2.GetAllUsersReply(users=self.users_list)

    def SendMessage(self, request, context) -> chat_pb2.SendMessageReply:
        """Sends message to user.

        Args:
            request: Request defined in chat.proto file.
            context: Grpc context.

        Returns:
            chat_pb2.SendMessageReply: Reply defined in chat.proto file.

        Raises grpc_error:
            grpc.StatusCode.NOT_FOUND: Raised when user to send message doesn't exist.
        """
        to_user = request.message.to_user_login
        from_user = request.message.from_user_login
        try:
            handler_to_send = EtcdMessagesHandler(client=self.etcd_client, to_user=to_user)
            handler_to_store = EtcdMessagesHandler(client=self.etcd_client, to_user=from_user)

        except KeyError as e:
            context.abort(grpc.StatusCode.NOT_FOUND, f"User {to_user} is do not exist")
            return chat_pb2.SendMessageReply()
        handler_to_send.add_message_to_queue(to_send_queue=True, value=MessageToJson(request.message))
        handler_to_store.add_message_to_queue(to_send_queue=False, value=MessageToJson(request.message))

        logging.debug(f"Message added to queue for user: {to_user}")
        return chat_pb2.SendMessageReply()

    def RecieveMessages(self, request, context) -> chat_pb2.RecieveMessagesReply:
        """Receives messages to user.
        
        When connection is active, takes messege from users queue and yield it
        till connected client get it.

        Also every 30 seconds yield empty message to help sinchronize client with server.

        Args:
            request: Request defined in chat.proto file.
            context: grpc context.

        Returns:
            chat_pb2.RecieveMessagesReply: Reply defined in chat.proto file.

        Yields:
            Iterator[chat_pb2.RecieveMessagesReply]: Iterate on reply defined in chat.proto file.
        
        Raises grpc_error
            grpc.StatusCode.UNAUTHENTICATED: When user who want to listen doesn't exist.
        """
        stream_to_user = request.to_user_login
        try:
            handler = EtcdMessagesHandler(client=self.etcd_client, to_user=stream_to_user)
        except KeyError as e:
            context.abort(
                grpc.StatusCode.UNAUTHENTICATED,
                f"User {stream_to_user} is not registred",
            )
            return chat_pb2.RecieveMessagesReply()
        
        response = handler.get_elems_from_queue(from_send_queue=False, 
                                                    get_all=True)
        for _, elem in response[-10:]:
            message = Parse(elem, chat_pb2.Message())
            yield chat_pb2.RecieveMessagesReply(message=message)
        logging.debug("[10 messeges from previous session restored]")
        while context.is_active():
            response = handler.get_elems_from_queue(from_send_queue=True, 
                                                    get_all=True)
            if not response:
                response = handler.get_elems_from_queue(from_send_queue=True, 
                                                        get_all=False, 
                                                        blocking=True, 
                                                        timeout=30)
                if not response:
                    # Sometimes send empty message to synch client thread
                    logging.debug("Timeout reached, sending synch message: [%s]")
                    yield chat_pb2.RecieveMessagesReply()
            else:
                for _, elem in response:
                    message = Parse(elem, chat_pb2.Message())
                    logging.debug(
                        "Message from: %s to %s, body: %s",
                        message.from_user_login,
                        message.to_user_login,
                        message.body.body,
                    )
                    yield chat_pb2.RecieveMessagesReply(message=message)
                handler.store_and_delete_sent_messages(response)
        logging.info("Stream to user %s ended", stream_to_user)
        return chat_pb2.RecieveMessagesReply()

    def RegisterUser(self, request, context) -> chat_pb2.RegisterUserReply:
        """Registers user

        Args:
            request: Request defined in chat.proto file.
            context: grpc context.
            
        Returns:
            chat_pb2.RegisterUserReply: Protobuf reply defined in chat.proto file.
        """
        auth = UserAuth(self.etcd_client)
        try:
            auth.register_user(request)
        except KeyError as e:
            context.abort(
                grpc.StatusCode.ALREADY_EXISTS,
                e,
            )
            return chat_pb2.RegisterUserReply()
        else:
            return chat_pb2.RegisterUserReply()
    
    def LoginUser(self, request, context) -> chat_pb2.LoginUserReply:
        """Logins user.

        Args:
            request: Request defined in chat.proto file.
            context: grpc context.

        Returns:
            chat_pb2.LoginUserReply: Protobuf reply defined in chat.proto file.
        """
        auth = UserAuth(self.etcd_client)
        try:
            auth.login_user(request)
        except KeyError as e:
            context.abort(
                grpc.StatusCode.UNAUTHENTICATED,
                e,
            )
            return chat_pb2.LoginUserReply()
        else:
            return chat_pb2.LoginUserReply()

def serve():
    port = "50051"
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chat_pb2_grpc.add_ChatServiceServicer_to_server(ChatServer(), server)
    server.add_insecure_port("[::]:" + port)
    logging.info("Server started, listening on [%s]", port)
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    serve()
