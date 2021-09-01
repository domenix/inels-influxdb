FROM python:3.9.6-alpine3.14

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

COPY . .

CMD ["sh", "-c", "python3 tcp_server.py"]

EXPOSE 65222