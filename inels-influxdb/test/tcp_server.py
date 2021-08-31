#!/usr/bin/env python3

import socket
import random
from time import sleep
from pathlib import Path
from loguru import logger
import sys

random.seed(42)

HOST = '127.0.0.1'
PORT = 65222

logger.add(sys.stderr, format="{time} {level} {message}", filter="*", level="INFO")
logger.add("logs/inels-imm-tester_{time}.log", rotation="2 MB", retention="8 days")

def wait_random(min=0.1, max=0.75):
    sleep(random.uniform(min, max))

position_file = ".position"
logged_events_file = "smart_home_logs"

smarthome_log_lines = []
with open(logged_events_file) as f:
    smarthome_log_lines = f.read().splitlines()

line_position = 0

if not Path(position_file).exists():
    Path(position_file).touch()
else:
    with open(position_file) as f:
        number = f.read()

        # Only assign number to line_position if it actually exists
        if number:
            line_position = int(number)


while True:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        logger.info(socket.gethostname())
        s.bind((socket.gethostname(), PORT))
        s.listen()
        logger.info("Waiting for connection...")
        conn, addr = s.accept()
        with conn:
            logger.info('Connected by', addr)
            while True:
                logger.info("Client finished ingesting, continuing, but wait a bit before")
                wait_random(1, 1.5)
                logger.info("Wait finished, sending")
                conn.sendall(f"{smarthome_log_lines[line_position]}\r\n".encode('ascii'))
                line_position += 1
                with open(position_file, 'w') as f:
                    f.write(str(line_position))


