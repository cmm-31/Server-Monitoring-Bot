# Server Monitoring Bot
import socket
import json
import requests
import argparse
import logging


parser = argparse.ArgumentParser()
parser.add_argument("-t", "--token", dest="token", help="set bot token")
parser.add_argument("-id", "--chat_id", dest="chat_id", help="set the chat_id")
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


servers_working = []
servers_not_working = []
hosts = [{"name": "electrumx-ch-1.feathercoin.ch", "port": 50001},
         {"name": "electrumx-de-2.feathercoin.ch", "port": 50001},
         {"name": "electrumxftc.trezarcoin.com", "port": 50001},
         {"name": "electrum.feathercoin.network", "port": 50001},
         {"name": "electrumx-gb-1.feathercoin.network", "port": 50001},
         {"name": "electrumx-gb-2.feathercoin.network", "port": 50001}]

# Running the code

for host in hosts:
    success = ping_server(host["name"], host["port"])
    if success:
        logging.debug("This server is up and running " + host["name"])
    else:
        message = "The following server(s) isn't/aren't responding properly. Please check this: " + host["name"]
        sendMessage(args.token, args.chat_id, message)
