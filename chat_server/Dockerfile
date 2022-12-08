FROM python:3.8

EXPOSE 50051

RUN mkdir /chat_server
VOLUME /chat_server/src

WORKDIR /chat_server/src

# COPY protobufs/ /service/protobufs/
# COPY chat_server/src /service/chat_server/src
# RUN python -m -I. --python_out=/service/chat_server/src --pyi_out=/service/chat_server/src \
#            --grpc_python_out=/service/chat_server/src protobufs/chat.proto
COPY requirements.txt .

RUN python -m pip install --upgrade pip
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-u", "./main.py"]
