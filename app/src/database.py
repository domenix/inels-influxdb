import queue
from threading import Thread, Event
from influxdb_client import WriteApi, WriteOptions
from influxdb_client.client.influxdb_client import InfluxDBClient
from loguru import logger
import datetime
import atexit
import socket
import time
import os
import utils


class DatabaseThread(Thread):
    def __init__(self, processed_events, db_addr, db_port, db_token, db_org, db_bucket):
        Thread.__init__(self)
        self.stop_event = Event()
        self.processed_events = processed_events
        self.db_addr = db_addr
        self.db_port = db_port
        self.db_token = db_token
        self.db_org = db_org
        self.db_bucket = db_bucket

    def get_name(self):
        return self.__class__.__name__

    def on_exit(self, db_client: InfluxDBClient, write_api: WriteApi):
        write_api.close()
        db_client.close()

    def line_protocol(self, event_id, source_id, value, **kwargs):
        timestamp = kwargs.get("timestamp", None)

        if timestamp is None:
            return f"home_sensors,event_id={event_id},source_id={source_id} value={value}"
        else:
            return f"home_sensors,event_id={event_id},source_id={source_id} value={value} {timestamp}"

    def get_current_in_ns(self, offset_seconds=0):
        curr_time = datetime.datetime.now(datetime.timezone.utc)
        offset_time = curr_time + datetime.timedelta(seconds=offset_seconds)
        return int(offset_time.timestamp() * 1000000000)

    def run(self):
        logger.debug("Thread execution started")

        retry_count = 0
        max_retries = 5
        wait_interval = 1

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # Retry if connection fails
            while not self.stop_event.is_set():
                if retry_count < max_retries:
                    try:
                        logger.info("Connecting to database at {}:{}", self.db_addr, self.db_port)
                        s.connect_ex((self.db_addr, self.db_port))
                        break
                    except (ConnectionResetError, ConnectionRefusedError, TimeoutError, socket.gaierror) as e:
                        logger.warning("Failed, retrying again in {} seconds, {} tries left (error: {})", wait_interval, max_retries - retry_count - 1, e)
                        time.sleep(wait_interval)
                        wait_interval = utils.get_new_wait_interval(wait_interval)
                        retry_count += 1
                        continue
                else:
                    logger.critical("Failed all retries, exiting")
                    os._exit(1)

        logger.info("Connected to database")
        # Wait until db connects
        _db_client = InfluxDBClient(url=f"http://{self.db_addr}:{self.db_port}", token=f"{self.db_token}", org=f"{self.db_org}")
        _write_api = _db_client.write_api(write_options=WriteOptions(batch_size=150, max_retry_time=2000))
        while not self.stop_event.is_set():
            try:
                queue_result = self.processed_events.get(True, 1)

                data = self.line_protocol(queue_result["event_id"], queue_result["source_id"], queue_result["event_value"], timestamp=self.get_current_in_ns())

                logger.debug("Inserting into database: {}", data)
                _write_api.write(bucket=f"{self.db_bucket}", record=data)
            except queue.Empty:
                continue

        logger.debug("Thread execution finished")
        atexit.register(self.on_exit, _db_client, _write_api)
