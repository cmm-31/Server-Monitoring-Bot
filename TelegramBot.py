# Server Monitoring Bot
import socket
import json
import requests
import argparse


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
    finally:
        sock.close()
    version_dict = json.loads(received)
    if "ElectrumX 1.5.1" in version_dict["result"]:
        return True
    else:
        return False


def sendMessage(token, chat_id, text):
    url = "https://api.telegram.org/bot{}/sendMessage".format(token)

    requests.post(url, data={"chat_id": chat_id, "text": text})


version = ping_server("electrumx-ch-1.feathercoin.ch", 50001)

sendMessage(args.token, args.chat_id, version)
