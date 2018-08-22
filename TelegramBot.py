# Server Monitoring Bot
import socket
import json
import argparse
import logging
import time
import datetime
import requests
from enum import Enum


def ping_server(HOST, PORT):
    # Create a socket (SOCK_STREAM means a TCP socket)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        sock.connect((HOST, PORT))
        sock.sendall(b'{"id": 2, "method": "server.version"}\n')
        received = sock.recv(1024)
    except Exception as e:
        logging.warning(e)
        return False

    finally:
        sock.close()
    version_dict = json.loads(received)
    return version_dict["result"][0].startswith("ElectrumX")


def sendMessage(token, chat_id, text):
    url = "https://api.telegram.org/bot{}/sendMessage".format(token)

    requests.post(url, data={"chat_id": chat_id, "text": text})

def gotofailed(host):
    message = "The following server isn't responding properly. Please check it: " + host["name"]
    sendMessage(args.token, args.chat_id, message)
    host["state"] = State.failed
    host["recheck_at"] = datetime.datetime.now() + datetime.timedelta(**recheck_duration)

class AutoNumber(Enum):
    def __new__(cls):
        value = len(cls.__members__) + 1
        obj = object.__new__(cls)
        obj._value_ = value
        return obj

class State(AutoNumber):
    running = ()
    failed = ()

parser = argparse.ArgumentParser()
parser.add_argument("-t", "--token", dest="token", help="set bot token")
parser.add_argument("-id", "--chat_id", dest="chat_id", help="set the chat_id")
parser.add_argument("-ho", "--hosts", dest="hosts", help="set the hosts")
parser.add_argument("-chec", "--recheck_duration", dest="recheck_duration", default="days:1", help="set the time until recheck")
parser.add_argument("-de", "--debug", dest="debug", default=False, type=bool, help="enable logging.debug if wanted")
parser.add_argument("-c", "--counter", dest="counter", default=5, type=int, help="set the check times, until the msg will be sent ")
args = parser.parse_args()

if args.debug == True:
    logging.basicConfig(level=logging.DEBUG)

hosts = []
for host in args.hosts.split(","):
    name, port = host.split(":")
    hosts.append({"name":name, "port":int(port), "state":State.running, "counter":0})


recheck_duration = {}
for duration in args.recheck_duration.split(","):
    unit, amount = duration.split(":")
    recheck_duration[unit] = int(amount)

while True:
    for host in hosts:
        success = ping_server(host["name"], host["port"])
        if success:
            logging.debug("This server is up and running " + host["name"])
        elif host["state"] == State.running:
            host["counter"] += 1
            logging.debug("Ping was not successful for " + host["name"])
            if host["counter"] == args.counter:
                gotofailed(host)

        if host["state"] == State.failed and host["recheck_at"] < datetime.datetime.now():
            logging.debug("Logging state is turned on running again for " + host["name"])
            host["state"] = State.running
            host["counter"] = 0
    time.sleep(10)
