import logging
from typing import List

import etcd
from google.protobuf.json_format import MessageToJson, Parse
from google.protobuf.timestamp_pb2 import Timestamp

from common import chat_pb2

from .helpers.hash import Hash


class UserAuth:
    """Class which implement auth operations for users with ETCD."""

    def __init__(self, client: etcd.Client) -> None:
        """Constructs user auth object.

        Args:
            client (etcd.Client): ETCD client.
        """
        logging.basicConfig(format="%(message)s", level=logging.INFO)
        self.client = client
        try:
            self.client.write("/users", None, dir=True, prevExist=False)
        except etcd.EtcdAlreadyExist:
            logging.debug("Dir users already created")

    def register_user(self, user: chat_pb2.RegisterUserRequest) -> None:
        """Creates user record in ETCD.

        Args:
            user (chat_pb2.RegisterUserRequest): Protobuf request from register user grpc call.

        Raises:
            KeyError: Raised when username is already registred
        """
        login = user.user_info.login
        try:
            self.client.write(
                f"/users/{login}", None, dir=True, prevExist=False
            )
        except etcd.EtcdAlreadyExist:
            raise KeyError(f"User {login} already registered")
        timestamp = Timestamp()
        timestamp.GetCurrentTime()
        info = chat_pb2.UserInfo(
            login=user.user_info.login,
            full_name=user.user_info.full_name,
        )
        user_info = chat_pb2.EtcdUserInfo(
            user_info=info,
            is_active=True,
            hashed_password=Hash.bcrypt(user.password),
            register_timestamp=timestamp.ToJsonString(),
        )
        self.client.write(
            f"/users/{login}/user_info",
            MessageToJson(user_info),
            prevExist=False,
        )
        logging.info("User %s registered successfully!", user)

    def login_user(self, user: chat_pb2.LoginUserRequest) -> None:
        """Authenticates user.

        Args:
            user (chat_pb2.LoginUserRequest):  Protobuf request from register user call.

        Raises:
            KeyError: Raised when authentication of user failed due to wrong password or nonexistance.
        """
        login = user.login
        try:
            res = self.client.read(f"/users/{login}/user_info")
        except etcd.EtcdKeyNotFound:
            raise KeyError(f"Login {login} failed")
        user_res: chat_pb2.EtcdUserInfo = Parse(
            res.value, chat_pb2.EtcdUserInfo()
        )
        if Hash.verify(
            hashed_password=user_res.hashed_password,
            plain_password=user.password,
        ):
            logging.info("User %s logged in successfully!", login)
        else:
            raise KeyError(f"Login {login} failed")

    def list_registered_users(self) -> List[chat_pb2.UserInfo]:
        """Returns all registers users.

        returns:
            List[chat_pb.UserInfo]: List of user info protobufs
        """
        res = self.client.read(f"/users", sorted=True)

        ret_list = []
        for lf in res.leaves:
            logging.info(lf.key)
            ret_list.append(
                Parse(
                    self.client.read(lf.key + "/user_info").value,
                    chat_pb2.EtcdUserInfo(),
                ).user_info
            )
        return ret_list
