from pathlib import Path
import argparse
import os
import sys
from loguru import logger
import threading


def is_file_readable(file_path):
    return is_file_valid(file_path, "r")


def is_file_writable(file_path):
    return is_file_valid(file_path, "a")


def is_file_valid(file_path, mode):
    path = Path(file_path).absolute()
    try:
        with open(path, mode):
            pass
        return path
    except IOError as e:
        raise argparse.ArgumentTypeError(f"'{file_path}' {os.strerror(e.errno)}")


def queue_log(unprocessed_queue_size, processed_queue_size):
    return f"Uprocessed event queue size: {unprocessed_queue_size}, processed event queue size: {processed_queue_size}"


def get_new_wait_interval(wait_interval, wait_ceiling=8):
    # Expoinential backoff
    if wait_interval == 1:
        return 2

    if wait_interval >= wait_ceiling:
        return wait_ceiling

    return wait_interval * 4


# Solution from https://stackoverflow.com/questions/6234405/logging-uncaught-exceptions-in-python
def handle_exception(exc_type, exc_value, exc_traceback, thread_identifier):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.opt(exception=True).critical(f"Uncaught exception in {thread_identifier}", exc_info=(exc_type, exc_value, exc_traceback))
    os._exit(1)


# Solution from https://cppsecrets.com/users/1334310010510711510497116105119971141055253485264103109971051084699111109/Python-Thread-based-parallelism-excepthook.php
def patch_threading_excepthook():
    old_init = threading.Thread.__init__

    def new_init(self, *args, **kwargs):
        old_init(self, *args, **kwargs)
        old_run = self.run

        def run_with_our_excepthook(*args, **kwargs):
            try:
                old_run(*args, **kwargs)
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                sys.excepthook(*sys.exc_info(), thread_identifier=threading.current_thread().name)

        self.run = run_with_our_excepthook

    threading.Thread.__init__ = new_init
