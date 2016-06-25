#!/usr/bin/env python3
import cmd
import readline
import select
import sys
import threading
import time
from socket import *  # import *, but we'll avoid name conflict


class ChatClientCMD(cmd.Cmd):
    intro = 'Welcome to the chat client.'
    prompt = '[Me] '
    file = None
    done = True

    def __init__(self, server, port, username):
        cmd.Cmd.__init__(self)

        self.server = server
        self.port = port
        self.username = username
        self.chat_client = None
        self.receive_thread = None
        self.connect = False

    @staticmethod
    def no_server():
        message = 'You are not connected to a server, use "\\connect" to connect to one.\n'
        post_message(message)

    @staticmethod
    def yes_server():
        message = 'You are already connected to a server, use "\\help" to to list commands.\n'
        post_message(message)

    def do_message(self, line):
        if self.connect:
            message = 'message ' + line
            self.chat_client.send_message(message)
        else:
            self.no_server()

    def do_listusers(self, line):
        if self.connect:
            message = 'username ' + line
            self.chat_client.send_message(message)
        else:
            self.no_server()

    def do_connect(self, line):
        if not self.connect:
            self.chat_client = ChatClient(self.server, self.port, self.username)
            self.connect = True
            self.receive_thread = ReceiveThread(self, self.chat_client)
            time.sleep(.1)
            self.receive_thread.start()
        else:
            self.yes_server()

    def do_disconnect(self, line):
        if self.connect:
            self.connect = False
            time.sleep(.1)
            self.chat_client.disconnect()
        else:
            self.no_server()

    def do_close(self, line):
        if self.connect:
            self.connect = False
            time.sleep(.1)
            self.chat_client.disconnect()
            return True
        else:
            return True

    def do_server(self, line):
        if not self.connect:
            split = line.split()
            self.server = split[0]
        else:
            self.yes_server()

    def do_port(self, line):
        if not self.connect:
            split = line.split()
            self.port = split[0]
        else:
            self.yes_server()

    def do_username(self, line):
        if not self.connect:
            split = line.split()
            self.username = split[0]
        else:
            self.yes_server()

    def precmd(self, line):
        if line and line[0] == '\\':
            line = line[1:]
        else:
            line = 'message ' + line
        return line

    def preloop(self):
        self.do_connect(None)


class ReceiveThread(threading.Thread):
    def __init__(self, chat_cmd, chat_client):
        threading.Thread.__init__(self)
        self.cmd = chat_cmd
        self.client = chat_client

    def run(self):
        while self.cmd.connect:
            message = self.client.receive_message()
            if message:
                tag, message = split_message(message)
                if tag == 'no_message':
                    pass
                elif tag == 'message':
                    tag, message = split_message(message)
                    post_message(message)
                elif tag == 'username':
                    self.username_list(message)
                elif tag == 'disconnection':
                    message_format = '{0} has disconnected.\n'
                    message = message_format.format(message)
                    post_message(message)
                elif tag == 'connection': 
                    message_format = '{0} has connected.\n'
                    message = message_format.format(message)
                    post_message(message)
                elif tag == 'error':
                    self.error_message(message)
                elif tag == 'shutdown':
                    post_message('Server had shutdown.\n')
                    self.client.disconnect()
                    self.cmd.connect = False
            else:
                self.client.disconnect()
                self.cmd.connect = False
                post_message('Lost connection to server.\n')

    @staticmethod
    def username_list(message):
        extras, message = split_message(message)
        split = message.strip().split()
        extras = int(split[0])
        usernames = split[1:]
        if extras == 0:
            message = ', '.join(usernames[:-1])
            message_format = 'The connected users are {0}, and {1}.\n'
            message = message_format.format(message, usernames[-1])
        else:
            message = ', '.join(usernames)
            message_format = 'The connected users are {0}, and {1} more.\n'
            message = message_format.format(message, extras)
        post_message(message)

    def error_message(self, message):
        tag, message = split_message(message)
        if tag == 'name_taken':
            self.client.close()
            self.cmd.connect = False
            message = 'Username {0} already taken, ust "\\username" to choose a new one'
            message.format(self.cmd.username)
            post_message(message)


def split_message(message):
    split = message.strip().split(sep=None, maxsplit=1)
    if len(split) < 2:
        return split[0], ''
    else:
        return split[0], split[1]


def post_message(message):
    temp = readline.get_line_buffer()
    sys.stdout.write('\r'+' '*(len(temp)+5)+'\r')
    sys.stdout.write(message)
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
        else:
            return 'no_message'

    def disconnect(self):
        self.sock.close()
        self.sock = None
