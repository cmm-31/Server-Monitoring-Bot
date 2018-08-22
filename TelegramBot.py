# Server Monitoring Bot
import socket
import json
import argparse
import logging
import time
import datetime
import requests

parser = argparse.ArgumentParser()
parser.add_argument("-t", "--token", dest="token", help="set bot token")
parser.add_argument("-id", "--chat_id", dest="chat_id", help="set the chat_id")
parser.add_argument("-ho", "--hosts", dest="hosts", help="set the hosts")
parser.add_argument("-chec", "--recheck_duration", dest="recheck_duration", default="days:1" help="set the time until recheck")
args = parser.parse_args()


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


hosts = []
for host in args.hosts.split(","):
    name, port = host.split(":")
    hosts.append({"name":name, "port":int(port), "state":"running"})


recheck_duration = {}
for duration in args.recheck_duration.split(","):
    unit, amount = duration.split(":")
    recheck_duration[unit] = int(amount)

while True:
    for host in hosts:
        success = ping_server(host["name"], host["port"])
        if success:
            logging.debug("This server is up and running " + host["name"])
        elif host["state"] == "running":
            message = "The following server isn't responding properly. Please check it: " + host["name"]
            sendMessage(args.token, args.chat_id, message)
            host["state"] = "failed"

            host["recheck_at"] = datetime.datetime.now() + datetime.timedelta(**recheck_duration)

        if host["state"] == "failed" and host["recheck_at"] < datetime.datetime.now():
            host["state"] = "running"
    time.sleep(10)
