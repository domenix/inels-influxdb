from threading import Thread, Event
from loguru import logger
import time
import socket
import os
import utils


class ConnectionThread(Thread):
    def __init__(self, unprocessed_events, addr, port):
        Thread.__init__(self)
        self.stop_event = Event()
        self.unprocessed_events = unprocessed_events
        self.addr = addr
        self.port = port

    def get_name(self):
        return self.__class__.__name__

    def run(self):
        logger.debug("Thread execution started")
        retry_count = 0
        max_retries = 5
        wait_interval = 1

        while not self.stop_event.is_set():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                # Retry if connection fails
                while not self.stop_event.is_set():
                    if retry_count < max_retries:
                        try:
                            logger.info("Connecting to iNELS CU at {}:{}", self.addr, self.port)
                            s.connect((self.addr, self.port))
                            break
                        except (ConnectionRefusedError, TimeoutError, socket.gaierror) as e:
                            logger.warning("Failed, retrying again in {} seconds, {} tries left (error: {})", wait_interval, max_retries - retry_count - 1, e)
                            time.sleep(wait_interval)
                            wait_interval = utils.get_new_wait_interval(wait_interval)
                            retry_count += 1
                            continue
                    else:
                        logger.critical("Failed all retries, exiting")
                        os._exit(1)

                wait_interval = 1
                retry_count = 0
                logger.info("Connected to iNELS CU")
                while not self.stop_event.is_set():
                    try:
                        logger.debug("Receiving data...")
                        s.settimeout(5.0)
                        data = s.recv(1024)
                    except (ConnectionAbortedError, ConnectionResetError):
                        logger.warning("Connection interrupted, reconnecting")
                        break

                    if len(data):
                        data_string = data.decode("ascii")
                        events = data_string.splitlines()

                        logger.debug("Bytes received: {}", data)

                        for event in events:
                            logger.debug("Inserting the following event into queue: {}", event)
                            self.unprocessed_events.put(event)

                    else:
                        # Retry reconnecting if empty bytes are being received
                        logger.warning("Connection interrupted, retrying")
                        break

        logger.debug("Thread execution finished")
