# Server Monitoring Bot
import argparse
import datetime
import json
import logging
import socket
import time
from enum import Enum

import requests


def send_message(token, chat_id, text):
    url = "https://api.telegram.org/bot{}/sendMessage".format(token)

    requests.post(url, data={"chat_id": chat_id, "text": text})


class Host():
    def __init__(self, owner, name, port, counter_limit,
                 token, chat_id, recheck_duration_para):
        self.name = name
        self.port = int(port)
        self.state = State.running
        self.counter = 0
        self.recheck_at = datetime.datetime.now()
        self.counter_limit = counter_limit
        self.token = token
        self.chat_id = chat_id
        self.recheck_duration_para = recheck_duration_para
        self.owner = owner

    def goto_state_failed(self):
        message = "{} Your server isn't responding properly. Please check {}"
        message = message.format(self.owner, self.name)
        send_message(self.token, self.chat_id, message)
        self.state = State.failed
        self.recheck_at = datetime.datetime.now() + datetime.timedelta(
            **self.recheck_duration_para)

    def ping_server(self):
        # Create a socket (SOCK_STREAM means a TCP socket)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            sock.connect((self.name, self.port))
            sock.sendall(b'{"id": 2, "method": "server.version"}\n')
            received = sock.recv(1024)

        except Exception as e:
            logging.warning(e)
            return False

        finally:
            sock.close()
        version_dict = json.loads(received)
        return version_dict["result"][0].startswith("ElectrumX")

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


class AutoNumber(Enum):
    def __new__(cls):
        value = len(cls.__members__) + 1
        obj = object.__new__(cls)
        obj._value_ = value
        return obj


class State(AutoNumber):
    running = ()
    failed = ()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--token", dest="token", help="set bot token")
    parser.add_argument("-id", "--chat_id", dest="chat_id",
                        help="set the chat_id")
    parser.add_argument("-ho", "--hosts", dest="hosts", help="set the hosts")
    parser.add_argument("-chec", "--recheck_duration", dest="recheck_duration",
                        default="days:1", help="set the time until recheck")
    parser.add_argument("-de", "--debug", dest="debug", default=False,
                        type=bool, help="enable logging.debug if wanted")
    parser.add_argument("-log", "--logfile", dest="logfile", default=False,
                        type=bool, help="logging.debug creates a file")
    parser.add_argument("-c", "--counter", dest="counter", default=5, type=int,
                        help="set the check times, until the msg will be sent")
    args = parser.parse_args()

    counter_limit = args.counter
    token = args.token
    chat_id = args.chat_id

    if args.debug and args.logfile:
        logging.basicConfig(filename="Logfile_debug", level=logging.DEBUG)
    elif args.debug:
        logging.basicConfig(level=logging.DEBUG)

    recheck_duration = {}
    for duration in args.recheck_duration.split(","):
        unit, amount = duration.split(":")
        recheck_duration[unit] = int(amount)

    recheck_duration_para = recheck_duration

    hosts = []
    for host in args.hosts.split(","):
        owner, name, port = host.split(":")
        hosts.append(Host(owner, name, port, counter_limit,
                          token, chat_id, recheck_duration_para))

    while True:
        for host in hosts:
            success = host.ping_server()
            if success:
                host.log_successful_ping()
            elif host.is_state_running():
                host.count_failed_ping()
                if host.reached_max_fails():
                    host.goto_state_failed()

            if host.reached_max_fails() and host.reached_rechecktime():
                host.goto_state_running()
        time.sleep(10)


main()
