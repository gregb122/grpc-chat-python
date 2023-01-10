import logging
from typing import List, Tuple

import etcd
from urllib3.exceptions import ReadTimeoutError


class EtcdMessagesHandler:
    """Class which implement queue operations for messages with ETCD."""

    def __init__(self, client: etcd.Client, to_user: str) -> None:
        """Construct all the necessary attributes for the object.

        Args:
            client (etcd.Client): ETCD client.
            to_user (str): Target user for queue

        Raises:
            KeyError: Raised when to_user is not registred.
        """
        logging.basicConfig(format="%(message)s", level=logging.INFO)

        self.client = client
        try:
            self.client.read(f"/users/{to_user}")
        except etcd.EtcdKeyNotFound:
            raise KeyError("User not found")
        self._to_send_str = f"/users/{to_user}/to_send_queue"
        self._sent_str = f"/users/{to_user}/sent_queue"

        try:
            client.write(self._to_send_str, None, dir=True, prevExist=False)
        except etcd.EtcdAlreadyExist:
            logging.debug("Dir to_send_queue already created")
        try:
            client.write(self._sent_str, None, dir=True, prevExist=False)
        except etcd.EtcdAlreadyExist:
            logging.debug("Dir sent_msgs already created")

    def add_message_to_queue(self, to_send_queue: bool, value: str) -> None:
        """Adds message to queue.

        Args:
            to_send_queue (bool): If true, then message will be added to send queue,
                                  If false, then message will be added to sent queue.
            value (str): Message string to store in queue.
        """
        self.client.write(
            self._to_send_str if to_send_queue else self._sent_str,
            value,
            append=True,
        )

    def get_elems_from_queue(
        self,
        from_send_queue: bool,
        get_all: bool = False,
        blocking: bool = False,
        timeout: int = None,
    ) -> List[Tuple[str, str]]:
        """Gets messeges from specific queue.

        Args:
            from_send_queue (bool): If true, then message will be taken from send queue,
                                    If false, then message will be taken from sent queue
            get_all (bool, optional): If True, then all elems of queue will be taken. Defaults to False.
            blocking (bool, optional): If True, then call will blocking. Defaults to False.
            timeout (int, optional): Timeout, how much time it will wait for message. If None, it will be infinity.
                                     Defaults to None.

        Returns:
            List[Tuple[str, str]]: List of pairs - ETCD key, message string.
        """
        try:
            res = self.client.read(
                self._to_send_str if from_send_queue else self._sent_str,
                recursive=True,
                wait=blocking,
                sorted=True,
                timeout=timeout,
            )
        except Exception:
            return []

        leaf = next(res.leaves)
        if leaf is res:
            return []
        first_elem = (leaf.key, leaf.value)
        if get_all:
            return [first_elem] + ([(lf.key, lf.value) for lf in res.leaves])
        return [first_elem]

    def store_and_delete_sent_messages(
        self, list_msg: List[Tuple[str, str]]
    ) -> None:
        """Stores messages in sent queue and deletes them from to send queue.

        Args:
            list_msg (List[Tuple[str, str]]): List of pairs - key, message string, where key is ETCD key.
        """
        for elem in list_msg:
            self.store_and_delete_sent_message(*elem)

    def store_and_delete_sent_message(self, key: str, value: str) -> None:
        """Stores one message in sent queue and delete it from to send queue.

        Args:
            key (str): ETCD key.
            value (str): Message string.
        """
        self.client.write(self._sent_str, value, append=True)
        self.client.delete(key)
