# gRPC terminal chat

`gRPC terminal chat` lets you easly host your own chat server and set up terminal chat clients with that one wierd friend :trollface:

## Contents

* [You can...](#you-can)
* [Installation](#installation)
* [Technology stack](#technology-stack)
* [Requirements](#requirements)
* [Server deployment](#server-deployment)
* [Client usage](#client-usage)

## You can

* [x] Register user
* [x] Send messages to other users
* [x] Get messages from many users at once
* [x] Get history of messages (Everyone have their own session)
* [x] Send messages to user even if he is offline.
* [x] Catch up with messages after login

`gRPC terminal chat` is the only tool that you need for **human interacions**.

## Installation

> **Warning**
> Writing to your friends about your secrets and wet dreams could be foolish, Security wasn't addressed yet. :triangular_flag_on_post:

### Get source

```sh
git clone https://github.com/Gregb122/grpc-terminal-chat.
```

## Technology stack

* **Python gRPC** powers client-server calls
* **Google protocolbuffers** Unified declaration of messages and code generation
* **ETCD** highly avaible and fast storage

## Requirements

* **ETCD** v2.3.7
* **Python** 3.8+

* **grpcio-tools** 1.51.1
* **python libs** defined in requirements.txt files

## Server deployment

### (Optional) How to create virual python env

You should put valid path to python interpreter(1st arg)

```sh
cd grpc-terminal-chat
virtualenv -p /usr/bin/python3.8 python_3.8_virtualenv
```

then ctivate:

```sh
source python_3.8_virtualenv/bin/activate
```

### How generate python protobuf files for server

Install grpc-tools to generate code from proto files

```sh
pip intall grpcio-tools
```

and then:

```sh
python3 -m grpc_tools.protoc -I. --python_out=chat_server/src --pyi_out=chat_server/src --grpc_python_out=chat_server/src protobufs/chat.proto
```

### How to run serwer localy

Run etcd2, you can do this with docker:

```sh
docker run --name etcd2 -d -p 2379:2379 -p 2380:2380 -p 4001:4001 -p 7001:7001 -v ~/temp/data0/etcd:/data wolfdeng/etcd2-docker

etcdctl --endpoints=http://<ip_of_etcd:2379> ls

```

install required python libs from requirements.txt:

```sh
pip install -r chat_server/requirements.txt
```

**run server:**

```sh
python3 chat_server/src/main.py
```

### Docker compose

```sh
docker-compose -f "docker_compose.yml" up
```

## Client usage

### How generate python protobuf files for client

Remember to install grpc-tools to generate code from proto files

```sh
pip intall grpcio-tools
```

and then:

```sh
python3 -m grpc_tools.protoc -I. --python_out=chat_client/src --pyi_out=chat_client/src --grpc_python_out=chat_client/src protobufs/chat.proto
```

### How to run client

Install required python libs from requirements.txt:

```sh
pip install -r chat_client/requirements.txt
```

To start the interactive program with default args, simply run:

```sh
python3 chat_client/src/main.py
```

---

`grpc-terminal-chat` was built with terminal in mind. You often can quit current scope by typing **/q**. Remember to register before login.
