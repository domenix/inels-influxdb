"""
EVENT 15 0x01050025 5824

EVENT text
event_id
source_id
value

"""

import queue
import re
from threading import Thread, Event
import yaml
from loguru import logger
import sys

# Currently, events that have unrecognized source_ids are stored in their original form
# If an event is not temperature or humidity, it is not modified in any way


class ParserThread(Thread):
    def __init__(self, unprocessed_events, processed_events, definitions_file, event_codes_file):
        Thread.__init__(self)
        self.stop_event = Event()
        self.unprocessed_events = unprocessed_events
        self.processed_events = processed_events
        self.config_lines = self.get_definitions(definitions_file)
        self.event_codes = self.get_event_codes(event_codes_file)

    def get_name(self):
        return self.__class__.__name__

    def is_def_valid(self, config_lines):
        # Lazy validity check
        # Check if line at least has two items and if the line has hex characters in it
        try:
            for config in config_lines:
                # Accessing nonexistent elements will cause IndexError to be raised
                config[0]
                config[1]

                # Check for existence of hex characters in any items on a line
                has_hex = False
                for item in config:
                    if "0x" in item:
                        has_hex = True
                        break

                if not has_hex:
                    raise ValueError
            return True
        except:
            return False

    def get_definitions(self, definitions_file):
        with open(definitions_file, encoding="utf-8-sig") as f:
            config_lines = [line.split() for line in f]

        if not self.is_def_valid(config_lines):
            logger.critical("Invalid event definitions, exiting")
            sys.exit(1)

        # Make all hex strings lowercase in the definitions
        hex_regex = r"0[xX][0-9a-fA-F]+"
        config_lines_lower = []
        for config in config_lines:
            new_config = []
            for item in config:
                if re.match(hex_regex, item):
                    item = item.lower()
                
                new_config.append(item)
                
            config_lines_lower.append(new_config)

        logger.debug("INELS BUS event definitions loaded")
        return config_lines_lower

    def get_event_codes(self, event_codes_file):
        with open(event_codes_file, "r") as stream:
            try:
                event_codes = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                logger.critical("Invalid event codes, exiting")
                sys.exit(1)

        logger.debug("INELS BUS event codes loaded")
        return event_codes

    def parse(self, inels_event):
        """
        Parses an inels event and returns a list with the correct data

        Parameters:
        inels_event (string): The inels_event required to be parsed

        Returns:
        list: Parsed inels_event elements in a list
        """

        # Test event string before processing
        event_format_regex = r"EVENT (?P<event_id>[0-9a-fA-F]+) (?P<source_id>0[xX][0-9a-fA-F]+) (?P<event_value>[0-9]+)"
        event_matched = re.match(event_format_regex, inels_event)
        if event_matched:
            orig_inels_event = event_matched.groupdict()
            inels_event = {}

            # Set textual event id before doing anything else
            inels_event["event_id"] = self.event_codes[orig_inels_event["event_id"].upper()]

            # Iterate over all config lines
            for config in self.config_lines:
                # Check if it matches a row
                config_source_id = config[1]

                # Incoming event source_id is in lowercase, but the config is in uppercase
                if orig_inels_event["source_id"] in config_source_id:
                    # Append class before doing anything else
                    # inels_event['event_id'] = orig_inels_event['event_id']

                    # Append name of config when matched in definitions file
                    human_readable_name = config[0]
                    inels_event["source_id"] = human_readable_name

                    # If the event is temperature or humidity or light, divide value by 100
                    last_config_item = config[-1]
                    if last_config_item == "°C" or last_config_item == "%" or "0x0108" in orig_inels_event["source_id"]:
                        inels_event["event_value"] = int(orig_inels_event["event_value"]) / 100
                    else:
                        # The value is neither temperature nor humidity, append event value unmodified
                        # Add extra modifications before this
                        inels_event["event_value"] = orig_inels_event["event_value"]

                    # Exit after first match
                    break

            # If we iterated over the whole list and there was no match for source_id, use original tokens
            else:
                inels_event["source_id"] = orig_inels_event["source_id"]
                inels_event["event_value"] = orig_inels_event["event_value"]

            return inels_event
        else:
            logger.warning("Match error, event: {}", inels_event)
            raise ValueError

    def run(self):
        logger.debug("Thread execution started")
        while not self.stop_event.is_set():
            try:
                queue_result = self.unprocessed_events.get(True, 1)
            except queue.Empty:
                continue

            try:
                parsed_result = self.parse(queue_result)
            except ValueError:
                # If there is a parse error, continue to next event
                continue

            logger.debug("Inserting the following parsed event into queue: {}", parsed_result)
            self.processed_events.put(parsed_result)
        logger.debug("Thread execution finished")
