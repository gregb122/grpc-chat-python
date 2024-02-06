FROM python:3.11

EXPOSE 50051

ENV ETCD_SERVER_IP_ADDR=${ETCD_SERVER_IP_ADDR}

COPY . /grpc_chat/chat_server/

WORKDIR /grpc_chat/
RUN ls
RUN ls chat_server
RUN ls chat_server/src
RUN python -m pip install --upgrade pip
RUN python -m pip install --no-cache-dir -r chat_server/requirements.txt

CMD ["python", "-u","-m", "chat_server.src.main"]