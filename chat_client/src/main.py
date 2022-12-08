import logging

import grpc
import protobufs.chat_pb2 as chat_pb2
import protobufs.chat_pb2_grpc as chat_pb2_grpc
from google.protobuf.timestamp_pb2 import Timestamp
from getpass import getpass


import chat_receiver


class ChatClient:
    """A class to represent a chat client object.

    ...

    Methods
    -------
    connect():
        Ask the user for login name and creates chat service stub,
        must be called before run().
    change_login_name():
        Change or set the user name
    run():
        Run chat client
    disconnect():
        Close channel, receiver thread and any other stuff opened.
        Must be called at the end of object existance.
    """

    def __init__(self, host: str, port: int) -> None:
        """Constructs all the necessary attributes for the client object.

        Parameters
        ----------
            host : str
                Host address(Address of the server)
            port : int
                Port number
        """
        self._is_connected = False

        self._channel = None
        self._stub = None
        self._receiver = None

        self._username = ""
        self._connection_addr = f"{host}:{port}"
        logging.debug("Chat client object created")

    def connect(self) -> None:
        """Ask for username and connect."""
        if self._is_connected:
            return
        try:
            self._channel = grpc.insecure_channel(self._connection_addr)
            self._stub = chat_pb2_grpc.ChatServiceStub(self._channel)
            self._handle_register()
            self._login()
        except ConnectionRefusedError as e:
            logging.error("Cannot connect [%s]", e)
        # except Exception as e:
        #     logging.error("Cannot connect [%s]", e)
        else:
            self._is_connected = True
            logging.info("Chat client connected")
        finally:
            self.disconnect()
            
    def _login(self) -> None:
        username =self._get_username()
        for _ in range(3):
            req = chat_pb2.LoginUserRequest(login=username, password=getpass())
            try:
                self._stub.LoginUser(request=req)
            except grpc.RpcError as rpc_error:
                if rpc_error.code() == grpc.StatusCode.UNAUTHENTICATED:
                    logging.info("Wrong creds, try again...", username)
                else:
                    raise rpc_error
            else:
                self._username = username
                return
        raise ConnectionRefusedError("Login failed")

    def _get_username(self) -> str:
        username = input("login: ").strip()
        while not username:
            username = input("login: ").strip()
            logging.info("Login cannot be blank")
        return username

    def run(self):
        """Run chat client"""
        if not self._is_connected:
            logging.error(
                "chat client is disconnected. (You have to call connect() before run())"
            )
            return

        self._open_stream_receiver()
        self._start_chat()
        self._close_stream_receiver()
        
    def _handle_register(self) -> None:
        for _ in range(3):
            if input("Do you want to register first? yes/[no]").strip().lower() in ["y", "yes"]:
                username = self._get_username()
                full_name = input("Full name:").strip()
                user_info = chat_pb2.UserInfo(login=username,full_name=full_name)
                req = chat_pb2.RegisterUserRequest(user_info=user_info, password=getpass())
                try:
                    self._stub.RegisterUser(request=req)
                except grpc.RpcError as rpc_error:
                    if rpc_error.code() == grpc.StatusCode.ALREADY_EXISTS:
                        logging.info("User %s already exists...", username)
                    else:
                        raise rpc_error
                else:
                    logging.info("u")
                    logging.info("User %s already exists", username)
                    return
            else:
                return
        logging.info("User %s register failed...", username)
        return
    
    def _log_avaible_users(self) -> None:
        response = self._stub.GetAllUsers(request=chat_pb2.GetAllUsersRequest())
        users_str = "".join(
            [f"{res.login} - {res.full_name}, " for res in response.users]
        )
        logging.info("Registered users: %s", users_str)

    def _open_stream_receiver(self) -> None:
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
        while True:
            user = input("\nType user to start chat with or /q to quit: \n").strip()
            if user == "/q":
                break
            if self._receiver.is_unauth():
                self._close_stream_receiver()
                break
            self._start_message_user(user)
            logging.info("Diconnected from chatroom with user: %s", user)
        logging.info("Quiting chat app...")

    def _start_message_user(self, user: str) -> None:
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
                self._open_stream_receiver()
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
                    self._log_avaible_users()
                    break

    def _create_message(
        self, user: str, text_to_send: str, timestamp: Timestamp
    ) -> chat_pb2.Message:
        timestamp.GetCurrentTime()
        body = chat_pb2.MessageBody(
            body=text_to_send, timestamp=timestamp.ToJsonString()
        )
        return chat_pb2.Message(
            from_user_login=self._username, to_user_login=user, body=body
        )

    def _log_chat_message(self, message: chat_pb2.Message) -> None:
        logging.info(
            "[%s] %s > %s",
            message.body.timestamp,
            message.from_user_login,
            message.body.body,
        )

    def disconnect(self) -> None:
        """Close any open connections"""
        if not self._is_connected:
            logging.error("You have to connect first...")
            return
        self._close_stream_receiver()
        self._channel.close()
        self._channel = None
        self._stub = None
        self._is_connected = False
        logging.info("Disconnected")

    def _close_stream_receiver(self) -> None:
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