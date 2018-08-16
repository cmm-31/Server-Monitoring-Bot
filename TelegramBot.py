# Server Monitoring Bot
import socket
import json
import requests
import argparse


parser = argparse.ArgumentParser()
parser.add_argument("-t", "--token", dest="token", help="set bot token")
args = parser.parse_args()
print(args.token)

def ping_server():
    HOST, PORT = "electrumx-ch-1.feathercoin.ch", 50001

    m = b'{"id": 2, "method": "server.version"}\n'
    jsonObj = json.loads(m)

    # Create a socket (SOCK_STREAM means a TCP socket)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Connect to server and send data
        sock.connect((HOST, PORT))
        #import pdb; pdb.set_trace()

        sock.sendall(m)

        # Receive data from the server and shut down
        received = sock.recv(1024)
        x = received
    finally:
        sock.close()
        return(x)


version_starter = ping_server()

version_dict = json.loads(version_starter)

version_list = version_dict["result"]

method = "sendMessage"
url = "https://api.telegram.org/bot{}/{}".format(args.token, method)


r = requests.post(url, data = {"chat_id": '@Bot_T1', "text": version_list})
