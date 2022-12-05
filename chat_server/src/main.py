import logging
import queue
from concurrent import futures
from typing import Dict, List

import time
import grpc
import protobufs.chat_pb2 as chat_pb2
import protobufs.chat_pb2_grpc as chat_pb2_grpc


class ChatServer(chat_pb2_grpc.ChatServiceServicer):
    """A class to represent a server object.

    Methods
    -------
    GetAllUsers():
        Returns registered users enpoint
    SendMessage():
        Send message to user endpoint
    RecieveMessages():
        Connect listener endpoint
    """

    def __init__(self) -> None:
        self.users_list: List[chat_pb2.UserInfo] = [
            chat_pb2.UserInfo(login="user1", full_name="User Someone"),
            chat_pb2.UserInfo(login="user2", full_name="User Someone2"),
        ]
        self.users_message_lists: Dict[str, queue.Queue] = {}

    def GetAllUsers(self, request, context) -> chat_pb2.GetAllUsersReply:
        """Get registred users.

        Parameters
        ----------
        request : chat_bp2.GetAllUsersRequest
            Request defined in chat.proto file
        context : grpc context

        Returns
        -------
        chat_pb2.GetAllUsersReply
            Reply defined in chat.proto file
        """
        logging.info("List all registred users")
        return chat_pb2.GetAllUsersReply(users=self.users_list)

    def SendMessage(self, request, context) -> chat_pb2.SendMessageReply:
        """Send message to user.

        Parameters
        ----------
        request : chat_bp2.SendMessageRequest
            Request defined in chat.proto file
        context : grpc context

        Returns
        -------
        chat_pb2.SendMessageReply
            Reply defined in chat.proto file

        Grpc_errors
        -------
        grpc.StatusCode.NOT_FOUND
            When user to send message doesn't exist
        grpc.StatusCode.RESOURCE_EXHAUSTED
            When message queue to user is full
        """
        to_user = request.message.to_user_login
        if not self._check_user(to_user):
            context.abort(grpc.StatusCode.NOT_FOUND, f"User {to_user} is do not exist")
            return chat_pb2.SendMessageReply()
        try:
            self.users_message_lists[to_user].put(request.message, block=False)
        except queue.Full as e:
            context.abort(
                grpc.StatusCode.RESOURCE_EXHAUSTED,
                f"Message queue for user {to_user} is full",
            )
            logging.debug(context.details())
        logging.debug(f"Message added to queue for user: {to_user}")
        # TODO: Save message to date store
        return chat_pb2.SendMessageReply()

    def RecieveMessages(self, request, context) -> chat_pb2.RecieveMessagesReply:
        """Receive messages to user.

        When connection is active, takes messege from users queue and yield it
        till connected client get it.

        Also every 30 seconds yield empty message to help sinchronize client with server.

        Parameters
        ----------
        request : chat_bp2.RecieveMessagesRequest
            Request defined in chat.proto file
        context : grpc context

        Returns
        -------
        chat_pb2.RecieveMessagesReply
            Reply defined in chat.proto file

        Grpc_errors
        -------
        grpc.StatusCode.UNAUTHENTICATED
            When user who want to listen doesn't exist
        """
        stream_to_user = request.to_user_login
        if not self._check_user(stream_to_user):
            context.abort(
                grpc.StatusCode.UNAUTHENTICATED,
                f"User {stream_to_user} is not registred",
            )
            return chat_pb2.RecieveMessagesReply()

        start = time.time()
        while context.is_active():
            try:
                message = self.users_message_lists[stream_to_user].get(block=False)
            except queue.Empty:
                if (
                    time.time() > start + 30
                ):  # Sometimes send empty message to synch client thread
                    start = time.time()
                    logging.debug("sending synch message: [%s]", start)
                    yield chat_pb2.RecieveMessagesReply()
                continue
            else:
                logging.debug(
                    "Message from: %s to %s, body: %s",
                    message.from_user_login,
                    message.to_user_login,
                    message.body.body,
                )
                yield chat_pb2.RecieveMessagesReply(message=message)
        logging.info("Stream to user %s ended", stream_to_user)
        return chat_pb2.RecieveMessagesReply()

    def _check_user(self, user: str) -> bool:
        logging.debug("User [%s] checking", user)
        if user not in self.users_message_lists:
            logging.debug("User [%s] has no message queue", user)
            if user not in [x.login for x in self.users_list]:
                logging.debug("User [%s] not registred", user)
                return False
            self.users_message_lists[user] = queue.Queue()
            return True
        return True


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
