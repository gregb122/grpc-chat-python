import logging

import grpc
import protobufs.chat_pb2 as chat_pb2
import protobufs.chat_pb2_grpc as chat_pb2_grpc
from google.protobuf.timestamp_pb2 import Timestamp
from getpass import getpass


import chat_receiver


class ChatClient:
    """A class to represent a chat client object.
    """
    def __init__(self, host: str, port: int) -> None:
        """Constructs all the necessary attributes for the client object.

        Args:
            host (str): Host address(Address of the server).
            port (int): Port number.
        """
        self._is_connected = False

        self._channel = None
        self._stub = None
        self._receiver = None

        self._username = ""
        self._connection_addr = f"{host}:{port}"
        logging.debug("Chat client object created")

    def connect(self) -> None:
        """Asks for username and connect.
        """
        if self._is_connected:
            return
        try:
            self._channel = grpc.insecure_channel(self._connection_addr)
            self._stub = chat_pb2_grpc.ChatServiceStub(self._channel)
            self._handle_register()
            self._handle_login()
        except ConnectionRefusedError as e:
            logging.error("Cannot connect [%s]", e)
        else:
            self._is_connected = True
            logging.info("Chat client connected")
        finally:
            self.disconnect()
            
    def _handle_login(self) -> None:
        """Handles user login, user is asked to provide username and password.
        User have 3 chances to input valid password.

        Raises:
            rpc_error: Raised when error type was not expected.
            ConnectionRefusedError: Raised when user provide wrong creds 3 times.
        """
        username =self._get_username()
        for _ in range(3):
            password = getpass()
            try:
                self._stub.LoginUser(request=chat_pb2.LoginUserRequest(login=username, 
                                                                       password=password))
            except grpc.RpcError as rpc_error:
                if rpc_error.code() == grpc.StatusCode.UNAUTHENTICATED:
                    logging.info("Login failed, username: s%", username)
                else:
                    raise rpc_error
            else:
                self._username = username
                return
        raise ConnectionRefusedError("Login failed")

    def _get_username(self) -> str:
        """Reads username from user.

        Returns:
            str: Username of the user.
        """
        username = input("username: ").strip()
        while not username:
            username = input("username: ").strip()
            logging.info("Username cannot be blank")
        return username

    def run(self):
        """Runs chat client.(Use connect(0) method before run(0)).
        """
        if not self._is_connected:
            logging.error(
                "chat client is disconnected. (You have to call connect(0) before run(0))"
            )
            return

        self._open_chat_receiver()
        self._start_chat()
        self._close_chat_receiver()
        
    def _handle_register(self) -> None:
        """Handles user register, takes username, full name and password from user.
        User have 3 chances to input valid password.

        Raises:
            rpc_error: Raised when error type was not expected.
        """
        if input("Do you want to register first? yes/[no]").strip().lower() in ["y", "yes"]:
            username = self._get_username()
            full_name = input("Full name:").strip()
            password = getpass()
            req = chat_pb2.RegisterUserRequest(user_info=chat_pb2.UserInfo(login=username,
                                                                           full_name=full_name),
                                               password=password)
            try:
                self._stub.RegisterUser(request=req)
            except grpc.RpcError as rpc_error:
                if rpc_error.code() == grpc.StatusCode.ALREADY_EXISTS:
                    logging.info("User %s already exists...", username)
                else:
                    raise rpc_error
            else:
                logging.info("User %s registered successfully", username)
                return
        else:
            return
    
    def _log_registred_users(self) -> None:
        """Logges registred users.
        """
        response = self._stub.GetAllUsers(request=chat_pb2.GetAllUsersRequest())
        users_str = "".join(
            [f"{res.login} - {res.full_name}, " for res in response.users]
        )
        logging.info("Registered users: %s", users_str)

    def _open_chat_receiver(self) -> None:
        """Helper method which handles chat receiver. 
        Checks if receiver is already created and is running.
        If not, it creates new.
        """
        logging.debug("Stream receiver connecting...")
        if self._receiver is not None:
            if not self._receiver.is_stopped():
                return
            else:
                self._receiver.join()
        response_iterator = self._stub.RecieveMessages(
            chat_pb2.RecieveMessagesRequest(to_user_login=self._username)
        )
        self._receiver = chat_receiver.ChatReceiver(response_iterator)
        self._receiver.start()

    def _start_chat(self) -> None:
        """Handles choose of user to message, it basicly main menu of the program.
        It starts infinity loop, then takes username who will be messaged and creates chat room.
        """
        while True:
            user = input("\nType user to start chat with or /q to quit: \n").strip()
            if user == "/q":
                break
            if self._receiver.is_unauth():
                self._close_chat_receiver()
                break
            self._start_message_user(user)
            logging.info("Diconnected from chatroom with user: %s", user)
        logging.info("Quiting chat app...")

    def _start_message_user(self, user: str) -> None:
        """Handles chat with user.

        Args:
            user (str): Target user to send chat messeges.
        """
        timestamp = Timestamp()
        logging.info("\nIf you want to quit chatroom, pls type /q")
        while True:
            text_to_send = input().strip()
            if not text_to_send:
                continue
            if text_to_send == "/q":
                break
            if self._receiver.is_stopped():
                logging.warning("Receiver stream closed, trying to reopen...")
                self._open_chat_receiver()
            if self._receiver.is_unauth():
                logging.error("User is not registred")
                return
            message = self._create_message(user, text_to_send, timestamp)
            try:
                self._stub.SendMessage(
                    request=chat_pb2.SendMessageRequest(message=message)
                )
            except grpc.RpcError as rpc_error:
                if rpc_error.code() == grpc.StatusCode.NOT_FOUND:
                    logging.info("User [%s] not found", user)
                    self._log_registred_users()
                    break

    def _create_message(
        self, user: str, text_to_send: str, timestamp: Timestamp
    ) -> chat_pb2.Message:
        """Creates protobuf message, and fills it with nesecary informations. 

        Args:
            user (str): Target user.
            text_to_send (str): String to send to target user.
            timestamp (Timestamp): Creation timestamp.

        Returns:
            chat_pb2.Message: Filled protobuf message.
        """
        timestamp.GetCurrentTime()
        body = chat_pb2.MessageBody(
            body=text_to_send, timestamp=timestamp.ToJsonString()
        )
        return chat_pb2.Message(
            from_user_login=self._username, to_user_login=user, body=body
        )

    def _log_chat_message(self, message: chat_pb2.Message) -> None:
        """Logges massege with correct human format.

        Args:
            message (chat_pb2.Message): protobuf message.
        """
        logging.info(
            "[%s] %s > %s",
            message.body.timestamp,
            message.from_user_login,
            message.body.body,
        )

    def disconnect(self) -> None:
        """Close any open connections.
        """
        if not self._is_connected:
            logging.error("You have to connect first...")
            return
        self._close_chat_receiver()
        self._channel.close()
        self._channel = None
        self._stub = None
        self._is_connected = False
        logging.info("Disconnected")

    def _close_chat_receiver(self) -> None:
        """Closes chat receiver.
        """
        if self._receiver is None:
            return
        self._receiver.s_stop()
        self._receiver.join()
        self._receiver = None


if __name__ == "__main__":
    logging.basicConfig(format="%(message)s", level=logging.DEBUG)

    chat_client = ChatClient("localhost", 50051)

    chat_client.connect()
    chat_client.run()
    chat_client.disconnect()
    exit()
