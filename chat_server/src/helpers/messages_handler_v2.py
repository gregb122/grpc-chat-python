import logging
from typing import List, Tuple

import etcd
from urllib3.exceptions import ReadTimeoutError


class EtcdMessagesHandler():
    def __init__(self, client: etcd.Client, to_user: str) -> None:
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
        
    def add_message_to_queue(self, to_send_queue:bool, value: str) -> None: 
        self.client.write(self._to_send_str if to_send_queue else self._sent_str,
                          value, 
                          append=True)
    
    def get_elems_from_queue(self,
                             from_send_queue:bool,
                             get_all: bool=False,
                             blocking: bool=False,
                             timeout: int=None) -> List[Tuple[str, str]]:
        try:
            res = self.client.read(self._to_send_str if from_send_queue else self._sent_str,
                                   recursive=True,
                                   wait=blocking,
                                   sorted=True,
                                   timeout=timeout)
        except Exception as e:
            return []
        
        leaf = next(res.leaves)
        if leaf is res:
            return []
        if get_all:
            return [(lf.key, lf.value) for lf in res.leaves]
        return [(leaf.key, leaf.value)]

    def delete_and_store_sent_messages(self, 
                                       list_msg: List[Tuple[str, str]]) -> None:
        for elem in list_msg:
            self._delete_and_store_sent_message(*elem)
            
    def _delete_and_store_sent_message(self, key: str, value: str) -> None:
        self.client.write(self._sent_str, value, append=True)
        self.client.delete(key)
