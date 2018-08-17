# Server Monitoring Bot
import socket
import json
import requests
import argparse


parser = argparse.ArgumentParser()
parser.add_argument("-t", "--token", dest="token", help="set bot token")
parser.add_argument("-id", "--chat_id", dest="chat_id", help="set chat_id")
args = parser.parse_args()
print(args.token)
print(args.chat_id)


def ping_server(HOST, PORT):

    m = b'{"id": 2, "method": "server.version"}\n'

    # Create a socket (SOCK_STREAM means a TCP socket)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        sock.connect((HOST, PORT))
        sock.sendall(m)

        received = sock.recv(1024)
    finally:
        sock.close()
    version_dict = json.loads(received)

    return bool(version_dict["result"])


version = ping_server("electrumx-ch-1.feathercoin.ch", 50001)


def sendMessage(token, chat_id, text):
    url = "https://api.telegram.org/bot{}/sendMessage".format(token)

    requests.post(url, data={"chat_id": chat_id, "text": text})


sendMessage(args.token, args.chat_id, version)
