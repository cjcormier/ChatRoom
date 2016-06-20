#!/usr/bin/env python3
from socket import *  # import *, but we'll avoid name conflict
import sys
import cmd
import threading

import select


class ChatClientCMD(cmd.Cmd):
    intro = 'Welcome to the chat client.'
    prompt = '[Me]'
    file = None
    done = True

    def __init__(self, server, port, username):
        cmd.Cmd.__init__(self)

        # self.server = server
        # self.port = port
        # self.username = username

        self.client = ChatClient(server, port, username)
        self.receiveThread = ReceiveThread(self, self.client)

    def default(self, message):
        self.client.send_message(message)
        self.receiveThread.run()

    def do_shell(self, arg):
        print(arg)

    def preloop(self):
        self.done = False

    def postloop(self):
        self.done = True


class ReceiveThread(threading.Thread):
    def __init__(self, chat_cmd, chat_client):
        threading.Thread.__init__(self)
        self.cmd = chat_cmd
        self.client = chat_client

    def run(self):
        while not self.cmd.run:
            message = self.client.receive_message
            print(message)
        print('Tread done')


class ChatClient:
    def __init__(self, server, port, username):
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.sock.connect((server, port))
        self.sock.send(username.encode())

    def send_message(self, message):
        message_len = self.sock.send(message.encode())

        if message_len != len(message):
            print("Failed to send complete message")

    def receive_message(self):
        read, write, err = select.select([self.sock], [], [], 0)
        if self.sock in read:
            return self.sock.recv(2 ** 16).strip()

    def loop(self):
        while True:
            sys.stdout.write('[Me] ')
            sys.stdout.flush()

            message = sys.stdin.readline().strip()
            self.send_message(message)

            message = self.receive_message()
            if message:
                sys.stdout.write(message.decode()+'\n')
                sys.stdout.flush()
