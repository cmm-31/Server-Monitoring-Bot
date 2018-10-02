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

    def __init__(self, name, port, counter_limit, recheck_duration):
        self.name = name
        self.port = int(port)
        self.state = State.running
        self.counter = 0
        self.recheck_at = datetime.datetime.now()
        self.counter_limit = counter_limit
        self.recheck_duration = recheck_duration

    def goto_state_failed(self):
        self.state = State.failed
        self.recheck_at = datetime.datetime.now() + datetime.timedelta(
            **self.recheck_duration)

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

    def goto_state_running(self):
        logging.debug(
            "Logging state is turned on running again for %s", self.name)
        self.state = State.running
        self.counter = 0

    def log_successful_ping(self):
        logging.debug("Ping was successful for %s", self.name)

    def is_state_running(self):
        return self.state == State.running

    def reached_rechecktime(self):
        return self.recheck_at < datetime.datetime.now()

    def reached_max_fails(self):
        return self.counter == self.counter_limit

    def count_failed_ping(self):
        self.counter += 1
        logging.debug("Ping was not successful for %s", self.name)


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
    parser.add_argument("-i", "--chat_id", dest="chat_id",
                        help="set the chat_id")
    parser.add_argument("-s", "--hosts", dest="hosts", help="set the hosts")
    parser.add_argument("-r", "--recheck_duration", dest="recheck_duration",
                        default="days:1", help="set the time until recheck")
    parser.add_argument("-d", "--debug", dest="debug", default=False,
                        type=bool, help="enable logging.debug if wanted")
    parser.add_argument("-l", "--logfile", dest="logfile", default=False,
                        type=bool, help="logging.debug creates a file")
    parser.add_argument("-c", "--counter", dest="counter", default=5, type=int,
                        help="set the check times, until the msg will be sent")
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
        services.append(Service(host=Host(name, port, args.counter,
                                          recheck_duration),
                                owner=owner))

    while True:
        for service in services:
            host = service.host
            success = host.ping_server()
            if success:
                host.log_successful_ping()
            elif host.is_state_running():
                host.count_failed_ping()
                if host.reached_max_fails():
                    host.goto_state_failed()
                    message = "{} Your server isn't responding properly"
                    message += " Please check {}"
                    message = message.format(service.owner, host.name)
                    send_message(args.token, args.chat_id, message)

            if host.reached_max_fails() and host.reached_rechecktime():
                host.goto_state_running()
        time.sleep(10)


main()
