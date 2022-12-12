import logging
import threading
from typing import Iterator

import grpc
import protobufs.chat_pb2 as chat_pb2


class ChatReceiver(threading.Thread):
    """Thread class which listen for incomming messages till stop(). The thread itself has to check
    regularly for the stopped() and set unauth condition on rpc_error UNAUTHENTICATED.
    """
    def __init__(
        self, response_iterator: Iterator[chat_pb2.RecieveMessagesReply]
    ) -> None:
        """Initialize chat receiver.

        Args:
            response_iterator (Iterator[chat_pb2.RecieveMessagesReply]):
                Response stream returned by stub RecieveMessages(1).
            
        """
        super(ChatReceiver, self).__init__()
        self._stop_event = threading.Event()
        self._unauth_event = threading.Event()
        self._response_iterator = response_iterator
        logging.basicConfig(format="%(message)s", level=logging.DEBUG)

    def run(self) -> None:
        """Run receiver and listen for messages on response iterator.
        """
        logging.debug("Stream started on another thread...")
        while not self.is_stopped():
            try:
                response = next(self._response_iterator)
            except grpc.RpcError as rpc_error:
                if rpc_error.code() == grpc.StatusCode.UNAUTHENTICATED:
                    logging.debug("User not registred...")
                    self._unauth_event.set()
                    return
                elif rpc_error.code() == grpc.StatusCode.CANCELLED:
                    logging.debug("Stream canceled by server...")
                elif rpc_error.code() == grpc.StatusCode.UNAVAILABLE:
                    logging.debug("Server unavaible...")
                self.s_stop()
                logging.error(rpc_error)
                return
            else:
                if response.HasField("message"):
                    logging.info(
                        "[%s] %s: %s",
                        response.message.body.timestamp[11:16],
                        response.message.from_user_login,
                        response.message.body.body,
                    )

        self._response_iterator.cancel()
        logging.debug("Stream canceled because user closed...")
        self.s_stop()

    def s_stop(self) -> None:
        """Set stop event flag.
        """
        self._stop_event.set()

    def is_stopped(self) -> bool:
        """Checks stop event flag.

        Returns:
            bool: true if stop flag is set.
        """
        return self._stop_event.is_set()

    def is_unauth(self) -> bool:
        """Checks if unauth event flag is set.

        Returns:
            bool: true if unauth flag is set.
        """
        return self._unauth_event.is_set()
