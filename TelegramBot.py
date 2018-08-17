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
    except Exception as e:
        return False

    finally:
        sock.close()
    version_dict = json.loads(received)
    if version_dict["result"][0].startswith("ElectrumX"):
        return True
    else:
        return False


def sendMessage(token, chat_id, text):
    url = "https://api.telegram.org/bot{}/sendMessage".format(token)

    requests.post(url, data={"chat_id": chat_id, "text": text})


host = "electrumx-ch-1.feathercoin.ch"
success = ping_server(host, 50001)

if success is True:
    message = "The server is up and running."
elif success is False:
    message = "The following Server isn't responding properly. Please check: " + host

sendMessage(args.token, args.chat_id, message)
