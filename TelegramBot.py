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


hosts_list = args.hosts.split(",")
hosts = []

for i in hosts_list:
    x = i.split(":")
    x[1] = int(x[1])
    tempo_dict = {}
    tempo_dict["name"] = x[0]
    tempo_dict["port"] = x[1]
    tempo_dict["state"] = "running"
    hosts.append(tempo_dict)

while True:
    for host in hosts:
        success = ping_server(host["name"], host["port"])
        if success:
            logging.debug("This server is up and running " + host["name"])
        elif host["state"] == "running":
            message = "The following server isn't responding properly. Please check it: " + host["name"]
            sendMessage(args.token, args.chat_id, message)
            host["state"] = "failed"

        host["recheck_at"] = datetime.datetime.now() + datetime.timedelta(seconds=30)

        if host["recheck_at"] > datetime.datetime.now():
            host["state"] = "running"
    time.sleep(10)
