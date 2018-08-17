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
        if version_dict["result"][0].startswith("lectrumX"):
            return True
        else:
            return False


def sendMessage(token, chat_id, text):
    url = "https://api.telegram.org/bot{}/sendMessage".format(token)

    requests.post(url, data={"chat_id": chat_id, "text": text})


servers_working = []
servers_not_working = []
hosts = ["electrumx-ch-1.feathercoin.ch", "electrumx-de-2.feathercoin.ch",
        "electrumxftc.trezarcoin.com", "electrum.feathercoin.network",
        "electrumx-gb-1.feathercoin.network", "electrumx-gb-2.feathercoin.network"]

for host in hosts:
    success = ping_server(host, 50001)
    if success is True:
        servers_working.append(host)
    else:
        servers_not_working.append(host)

servers_not_working_str = ''.join(map(str, servers_not_working))

if success is True:
    message = "The servers  are up and running."
else:
    message = "The following server(s) isn't/aren't responding properly. Please check this: " + servers_not_working_str

sendMessage(args.token, args.chat_id, message)
