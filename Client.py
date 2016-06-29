#!/usr/bin/env python3
import argparse

from ChatRoom.ClientUI import *

parser = argparse.ArgumentParser(description='Chat room client')
parser.add_argument('--server', help='ip of the chat room server')
parser.add_argument('--port', help='port of the chat room server', type=int)
parser.add_argument('--username', help='username to use when connection to the chat room')

args = parser.parse_args()

server = ''
if args.server:
    server = args.server
else:
    server = input('Server:').strip()

port = 0
if args.port:
    port = args.port
else:
    port = int(input('Port:'))

username = ''
if args.username:
    username = args.username
else:
    username = input('Username:').strip()


def main():
    ChatClientCMD(server, port, username).cmdloop()

if __name__ == '__main__':
    sys.exit(main())

