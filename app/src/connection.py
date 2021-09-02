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


        while not self.stop_event.is_set():
            socket_retry_count = 0
            socket_max_retries = 5
            socket_wait_interval = 1
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(5)

                    while not self.stop_event.is_set():
                        retry_count = 0
                        max_retries = 5
                        wait_interval = 1
                        if retry_count < max_retries:
                            try:
                                logger.info("Connecting to iNELS CU at {}:{}", self.addr, self.port)
                                s.connect((self.addr, self.port))
                                s.settimeout(None)
                                break
                            except (ConnectionRefusedError, TimeoutError, socket.gaierror) as e:
                                s.settimeout(None)
                                # s.settimeout(5)
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
            except socket.timeout as e:
                if socket_retry_count < socket_max_retries:
                    logger.warning("Failed during socket creation, retrying again in {} seconds, {} tries left (error: {})", socket_wait_interval, socket_max_retries - socket_retry_count - 1, e)
                    time.sleep(socket_wait_interval)
                    socket_wait_interval = utils.get_new_wait_interval(socket_wait_interval)
                    socket_retry_count += 1
                else:
                    logger.critical("Failed all retries, exiting")
                    os._exit(1)

        logger.debug("Thread execution finished")
