#!/usr/bin/env python3
import cmd
import readline
import select
import sys
import threading
from socket import *  # import *, but we'll avoid name conflict


class ChatClientCMD(cmd.Cmd):
    intro = 'Welcome to the chat client.'
    prompt = '[Me] '
    file = None
    done = True

    def __init__(self, chat_client):
        cmd.Cmd.__init__(self)

        self.chat_client = chat_client
        self.receive_thread = ReceiveThread(self, self.chat_client)

    def default(self, line):
        pass

    def do_message(self, line):
        self.chat_client.send_message(line)

    def precmd(self, line):
        if line[0] == '\\':
            line = line[1:]
        else:
            line = 'message ' + line
        return line

    def preloop(self):
        self.done = False
        self.receive_thread.start()

    def postloop(self):
        self.done = True


class ReceiveThread(threading.Thread):
    def __init__(self, chat_cmd, chat_client):
        threading.Thread.__init__(self)
        self.cmd = chat_cmd
        self.client = chat_client

    def run(self):
        while not self.cmd.done:
            message = self.client.receive_message()
            if message:
                temp = readline.get_line_buffer()
                sys.stdout.write('\r'+' '*(len(temp)+4)+'\r')
                print(message)
                sys.stdout.write('[Me] '+temp)
                sys.stdout.flush()


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
