from connection import ConnectionThread
from inels_parser import ParserThread
from database import DatabaseThread
import queue
import time
import sys
from loguru import logger
import argparse
import utils
import signal
import os

# Handle SIGTERM from Docker, solution from https://lemanchet.fr/articles/gracefully-stop-python-docker-container.html
def handle_sigterm(*args):
    raise KeyboardInterrupt()


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, handle_sigterm)

    parser = argparse.ArgumentParser(description="Connect to iNELS CU telnet port and dump the events to an InfluxDB database.")
    parser.add_argument("-a", "--addr", required=True, help="IP address of the iNELS CUM server")
    parser.add_argument("-p", "--port", default=1111, type=int, help="Telnet port of the iNELS CU server (default: %(default)s)")

    parser.add_argument("-d", "--defs", type=utils.is_file_readable, required=True, help="Path to the event definitions file (e.g. export.imm)")
    parser.add_argument("-c", "--codes", default="event_codes.yml", type=utils.is_file_readable, help="Path to the event codes file (default: %(default)s)")

    parser.add_argument("-da", "--dbaddr", required=True, help="IP address of the database")
    parser.add_argument("-dp", "--dbport", default=8086, type=int, help="Port of the database (default: %(default)s)")
    parser.add_argument("-dt", "--dbtoken", required=True, help="Database token")
    parser.add_argument("-do", "--dborg", required=True, help="Database organization")
    parser.add_argument("-b", "--bucket", required=True, help="Database bucket")

    args = parser.parse_args()

    addr = args.addr
    port = args.port
    defs = args.defs
    codes = args.codes
    dbaddr = args.dbaddr
    dbport = args.dbport
    dbtoken = args.dbtoken
    dborg = args.dborg
    bucket = args.bucket

    log_config = {
        "handlers": [
            {"sink": sys.stderr, "format": "{time} - {level} - {message}"}
        ]
    }

    RUNNING_INSIDE_DOCKER = os.environ.get('RUNNING_INSIDE_DOCKER')
    if not (RUNNING_INSIDE_DOCKER and RUNNING_INSIDE_DOCKER == '1'):
        log_config['handlers'].append(
            {"sink": "logs/inels-influxdb_{time}.log", "format": "{time} - {level} - {message}",  "rotation": "2 MB", "retention": "8 days"}
        )

    logger.configure(**log_config)

    logger.info("inels-influxdb started")

    # There are two queues, one that has unprocessed events
    # and acts as an intermediary between the connection thread
    # and the parser thread.
    # The other thread holds processed events, which acts as
    # an intermediary between the parser thread and the
    # database thread
    # The goal is to decouple the main thread from all of the event
    # parsing and act only as an entity that kicks off everything else

    work_threads = []
    unprocessed_events = queue.Queue()
    processed_events = queue.Queue()

    connection_thread = ConnectionThread(unprocessed_events, addr, port)
    parser_thread = ParserThread(unprocessed_events, processed_events, defs, codes)
    database_thread = DatabaseThread(processed_events, dbaddr, dbport, dbtoken, dborg, bucket)

    work_threads.append(connection_thread)
    work_threads.append(parser_thread)
    work_threads.append(database_thread)

    for work_thread in work_threads:
        work_thread.start()

    # Solution from https://stackoverflow.com/a/66949660/2581807
    while True:
        try:
            time.sleep(0.5)
            unprocessed_queue_size = unprocessed_events.qsize()
            processed_queue_size = processed_events.qsize()

            # Print queue sizes if they have more than 1 items queued up
            if unprocessed_queue_size > 1 and unprocessed_queue_size < 10 or processed_queue_size > 1 and processed_queue_size < 10:
                logger.debug(utils.queue_log(unprocessed_queue_size, processed_queue_size))
            elif unprocessed_queue_size >= 10 and unprocessed_queue_size < 50 or processed_queue_size >= 10 and processed_queue_size < 50:
                logger.warning(utils.queue_log(unprocessed_queue_size, processed_queue_size))
            elif unprocessed_queue_size >= 50 and unprocessed_queue_size < 100 or processed_queue_size >= 50 and processed_queue_size < 100:
                logger.error(utils.queue_log(unprocessed_queue_size, processed_queue_size))
            elif unprocessed_queue_size >= 100 and unprocessed_queue_size < 250 or processed_queue_size >= 100 and processed_queue_size < 250:
                logger.critical(utils.queue_log(unprocessed_queue_size, processed_queue_size))
            elif unprocessed_queue_size >= 500 or processed_queue_size >= 500:
                logger.critical(utils.queue_log(unprocessed_queue_size, processed_queue_size))
                raise KeyboardInterrupt

        except KeyboardInterrupt:
            # Graceful shutdown
            logger.debug("Shutting down, working threads left: {}", len(work_threads))
            for work_thread in work_threads:
                if work_thread.is_alive():
                    logger.debug("Work thread {}: setting STOP event", work_thread)
                    work_thread.stop_event.set()
                    logger.debug("Work thread {}: joining to Main", work_thread)
                    work_thread.join()
                    logger.debug("Work thread {}: joined to Main", work_thread)
                else:
                    logger.debug("Work thread {} has died", work_thread)
            logger.info("inels-influxdb exiting")
            sys.exit(0)
