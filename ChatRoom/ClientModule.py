#!/usr/bin/env python3
import select
from socket import *  # import *, but we'll avoid name conflict


class ChatClient:
    def __init__(self, server, port, username):
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.sock.connect((server, port))
        self.sock.send(username.encode())

    def check(self):
        to_read = list(sys.stdin)
        read, write, err = select.select(to_read, [], [], 0)
        if sys.stdin in read:
            return sys.stdin.readline
        else:
            self.receive_message()
            return ''

    def send_message(self, message):
        message_len = self.sock.send(message.encode())

        if message_len != len(message):
            print("Failed to send complete message")

    def receive_message(self):
        read, write, err = select.select([self.sock], [], [], 0)
        if self.sock in read:
            return self.sock.recv(2 ** 16).strip().decode()
        else:
            return 'no_message'

    def disconnect(self):
        self.sock.close()
        self.sock = None
