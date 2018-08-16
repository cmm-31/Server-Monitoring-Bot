# Server Monitoring Bot
import socket
import json
import requests
import argparse


parser = argparse.ArgumentParser()
parser.add_argument("-t", "--token", dest="token", help="set bot token")
args = parser.parse_args()
print(args.token)

def ping_server(HOST, PORT):
    HOST, PORT = "electrumx-ch-1.feathercoin.ch", 50001

    m = b'{"id": 2, "method": "server.version"}\n'

    # Create a socket (SOCK_STREAM means a TCP socket)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Connect to server and send data
        sock.connect((HOST, PORT))
        #import pdb; pdb.set_trace()

        sock.sendall(m)

        # Receive data from the server and shut down
        received = sock.recv(1024)
    finally:
        sock.close()
    version_dict = json.loads(received)
    return version_dict["result"]


version = ping_server("electrumx-ch-1.feathercoin.ch", 50001)

def sendMessage(token, chat_id, text):
    url = "https://api.telegram.org/bot{}/sendMessage".format(token)

    r = requests.post(url, data = {"chat_id": chat_id, "text": text})


sendMessage(args.token, '@Bot_T1', version)
