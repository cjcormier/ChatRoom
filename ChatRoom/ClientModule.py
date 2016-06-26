#!/usr/bin/env python3
import cmd
import readline
import select
import sys
import threading
import time
from socket import *  # import *, but we'll avoid name conflict


class ChatClientCMD(cmd.Cmd):
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
    def no_server(verbose=True):
        message = 'You are not connected to a server.'
        if verbose:
            message += 'Use "\\connect" to connect to one or "\\help" to to list commands'
        message += '\n'
        post_message(message, True)

    @staticmethod
    def yes_server(verbose=True):
        message = 'You are already connected to a server.'
        if verbose:
            message += 'Use "\\disconnect" to disconnect or "\\help" to to list commands.'
        message += '\n'
        post_message(message, True)

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
            try:
                self.chat_client = ChatClient(self.server, self.port, self.username)
            except ConnectionRefusedError:
                message_format = 'ERROR: Connection to {0}:{1} refused. Unable to connect\n'
                message = message_format.format(self.server, self.port)
                post_message(message, True)
            else:
                self.connect = True
                self.receive_thread = ReceiveThread(self, self.chat_client)
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

    def do_serverinfo(self, line):
        message = 'Connected to {0}:{1} as {2}\n'.format(self.server, self.port, self.username)
        post_message(message)

    def do_port(self, line):
        if not self.connect:
            split = line.split()
            self.port = int(split[0])
        else:
            self.yes_server()

    def do_whisper(self, line):
        if self.connect:
            message = 'whisper ' + line
            self.chat_client.send_message(message)
        else:
            self.no_server()

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
        post_message('Welcome to the chat client.', True)
        self.do_connect(None)


class ReceiveThread(threading.Thread):
    def __init__(self, chat_cmd, chat_client):
        threading.Thread.__init__(self)
        self.cmd = chat_cmd
        self.client = chat_client

    def run(self):
        time.sleep(.1)
        while self.cmd.connect:
            message = self.client.receive_message()
            if message:
                tag, message = split_message(message)
                if tag == 'no_message':
                    pass
                elif tag == 'message':
                    username, message = split_message(message)
                    message_format = '[{0}] said: {1}\n'
                    message = message_format.format(username, message)
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
                    post_message('Server has shutdown.\n')
                    self.client.disconnect()
                    self.cmd.connect = False
                elif tag == 'whisper':
                    username, message = split_message(message)
                    message_format = '[{0}] whispers: {1}\n'
                    message = message_format.format(username, message)
                    post_message(message)
            else:
                self.client.disconnect()
                self.cmd.connect = False
                post_message('Lost connection to server.\n')

    def username_list(self, message):
        extras, usernames = split_message(message)
        extras = int(extras)
        usernames = usernames.split()
        if extras == 0:
            if len(usernames) == 1:
                message = usernames
                message_format = 'You, {0}, are the only user connected.\n'
            elif len(usernames) == 2:
                usernames.remove(self.cmd.username)
                message = usernames[0]
                message_format = 'You and {0} are the only users connected.\n'
            else:
                message = ', '.join(usernames[:-1])
                message_format = 'The connected users are {0}, and {1}.\n'
            message = message_format.format(message, usernames[-1])
        else:
            message = ', '.join(usernames)
            message_format = 'The connected users are {0}and {1} more.\n'
            message = message_format.format(message, extras)
        post_message(message)

    def error_message(self, message):
        tag, message = split_message(message)
        if tag == 'name_taken':
            self.client.disconnect()
            self.cmd.connect = False
            message_format = 'ERROR: Username {0} already taken, use "\\username" to choose a new one.\n'
            message = message_format.format(self.cmd.username)
            post_message(message)
        elif tag == 'no_name_whisper':
            message_format = 'ERROR: Unable to whisper, user {0} not found.\n'
            message = message_format.format(message)
            post_message(message)
            

def split_message(message):
    split = message.strip().split(sep=None, maxsplit=1)
    if len(split) < 2:
        return split[0], ''
    else:
        return split[0], split[1]


def post_message(message, from_cmd=False):
    temp = readline.get_line_buffer()
    sys.stdout.write('\r'+' '*(len(temp)+5)+'\r')
    sys.stdout.write(message)
    if not from_cmd:
        sys.stdout.write('[Me] ' + temp)
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
