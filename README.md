# grpc-terminal-chat

## How generate python protobuf files
> python3 -m grpc_tools.protoc -I. --python_out=chat_server/src --pyi_out=chat_server/src --grpc_python_out=chat_server/src protobufs/chat.proto
> python3 -m grpc_tools.protoc -I. --python_out=chat_client/src --pyi_out=chat_client/src --grpc_python_out=chat_client/src protobufs/chat.proto

## How to run serwer localy, other options - WIP
> python3.8 chat_server/src/main.py

## How to run client
> python3.8 chat_client/src/main.py
