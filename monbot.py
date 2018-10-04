# Server Monitoring Bot
import argparse
import datetime
import json
import logging
import socket
import time
from collections import namedtuple
from enum import Enum

import requests


def send_message(token, chat_id, text):
    url = "https://api.telegram.org/bot{}/sendMessage".format(token)

    requests.post(url, data={"chat_id": chat_id, "text": text})


class Host():
    """Host is a class representing the server."""

    def __init__(self, name, port, max_retries, recheck_duration):
        self.name = name
        self.port = int(port)
        self.state = State.running
        self.retries = 0
        self.recheck_at = datetime.datetime.now()
        self.max_retries = max_retries
        self.recheck_duration = recheck_duration

    def ping_server(self):
        sock = None
        try:
            sock = socket.create_connection((self.name, self.port), 5)
            sock.sendall(b'{"id": 2, "method": "server.version"}\n')
            response = json.loads(sock.recv(1024))
            return response["result"][0].startswith("ElectrumX")
        # pylint: disable=broad-except
        except Exception as error:
            logging.warning(error)
            return False
        finally:
            if sock is not None:
                sock.close()

    def is_failed(self):
        transition_to_running = self.recheck_at < datetime.datetime.now()
        if transition_to_running and self.state != State.running:
            logging.debug("state transition into running for %s", self.name)
            self.state = State.running
            self.retries = 0
        return self.state == State.failed

    def is_retrying(self):
        self.retries += 1
        logging.debug("encountered failure for %s", self.name)
        if self.retries < self.max_retries:
            return True
        if self.state != State.failed:
            logging.debug("state transition into failed for %s", self.name)
            self.state = State.failed
            self.recheck_at = datetime.datetime.now() + datetime.timedelta(
                **self.recheck_duration)
        return False


class State(Enum):
    """State is an enum class representing the state of the server."""

    def __new__(cls):
        obj = object.__new__(cls)
        # pylint: disable=protected-access
        obj._value_ = len(cls.__members__) + 1
        return obj

    running = ()
    failed = ()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--token", dest="token", help="set bot token")
    parser.add_argument("-c", "--chat_id", dest="chat_id",
                        help="set the chat_id")
    parser.add_argument("-s", "--hosts", dest="hosts", help="set the hosts")
    parser.add_argument("-r", "--recheck_duration", dest="recheck_duration",
                        default="days:1", help="set the time until recheck")
    parser.add_argument("-d", "--debug", dest="debug", default=False,
                        type=bool, help="enable logging.debug if wanted")
    parser.add_argument("-l", "--logfile", dest="logfile", default=False,
                        type=bool, help="logging.debug creates a file")
    parser.add_argument("-m", "--max-retries", dest="max_retries", default=5,
                        type=int, help="the number of retries upon failure")
    args = parser.parse_args()

    if args.debug and args.logfile:
        logging.basicConfig(filename="Logfile_debug", level=logging.DEBUG)
    elif args.debug:
        logging.basicConfig(level=logging.DEBUG)

    recheck_duration = {}
    for duration in args.recheck_duration.split(","):
        unit, amount = duration.split(":")
        recheck_duration[unit] = int(amount)

    Service = namedtuple('Service', ['host', 'owner'])
    services = []
    for host in args.hosts.split(","):
        owner, name, port = host.split(":")
        services.append(Service(host=Host(name, port, args.max_retries,
                                          recheck_duration),
                                owner=owner))

    while True:
        for service in services:
            host = service.host
            if host.is_failed():
                continue
            if not host.ping_server() and not host.is_retrying():
                message = "{} Your server isn't responding properly"
                message += " Please check {}"
                message = message.format(service.owner, host.name)
                send_message(args.token, args.chat_id, message)

        time.sleep(10)


main()
