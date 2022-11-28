import logging
import threading
from typing import Iterator

import grpc
import protobufs.chat_pb2 as chat_pb2


class ChatReceiver(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self, response_iterator: Iterator[chat_pb2.RecieveMessagesReply]):
        super(ChatReceiver, self).__init__()
        self._stop_event = threading.Event()
        self._unauth_event = threading.Event()
        self._response_iterator = response_iterator
        logging.basicConfig(format='%(message)s', level=logging.DEBUG)

    def run(self) -> None: 
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
                    self.s_stop()
                    return
                elif rpc_error.code() == grpc.StatusCode.UNAVAILABLE:
                    logging.debug("Server unavaible...")
                    self.s_stop()
                    return
                logging.error(rpc_error)
            else:
                if response.HasField("message"):
                    logging.info("[%s] %s: %s",
                                 response.message.body.timestamp[11:16],
                                 response.message.from_user_login,
                                 response.message.body.body)
                    
        self._response_iterator.cancel()
        logging.debug("Stream canceled because user closed...")
        self.s_stop()
    
    def s_stop(self):
        self._stop_event.set()

    def is_stopped(self):
        return self._stop_event.is_set()
    
    def is_unauth(self):
        return self._unauth_event.is_set()
