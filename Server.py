#!/usr/bin/env python
import argparse
from ChatRoom.ServerModule import ChatServer
import sys
# import logging

parser = argparse.ArgumentParser(description='Chat room Server')
parser.add_argument('port', help='the port to listen on', type=int)
# parser.add_argument('--verbose', help='increase verbosity', action='store_true')

args = parser.parse_args()
server = ChatServer(args.port)


def main():
    while True:
        server.loop()

if __name__ == '__main__':
    sys.exit(main())
