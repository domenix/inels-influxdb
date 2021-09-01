from pathlib import Path
import argparse
import os


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
