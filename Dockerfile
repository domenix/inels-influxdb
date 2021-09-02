FROM python:3.9.6-alpine3.14

WORKDIR /app

COPY LICENSE LICENSE

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

COPY app/src .

ENV RUNNING_INSIDE_DOCKER=1

CMD ["sh", "-c", "python3 main.py -a ${SERVER_ADDRESS} -p ${SERVER_PORT} -d /inels_data/export.imm -c /inels_data/event_codes.yml -da ${DB_ADDRESS} -dp ${DB_PORT} -dt ${DB_TOKEN} -do ${DB_ORG} -b ${BUCKET}"]
