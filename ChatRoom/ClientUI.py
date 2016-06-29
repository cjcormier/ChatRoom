#!/usr/bin/env python3
import threading
import time
import cmd
from .ClientModule import *


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
        """Informs the user that the command is invalid because
        they are not connected to the server
        """
        message = 'You are not connected to a server.'
        if verbose:
            message += 'Use "\\connect" to connect to one or ' \
                       '"\\help" to to list commands'
        message += '\n'
        post_message('[Me] ', message, True)

    @staticmethod
    def yes_server(verbose=True):
        """Informs the user that the command is invalid because
        they are already connected to the server
        """
        message = 'You are already connected to a server.'
        if verbose:
            message += 'Use "\\disconnect" to disconnect or ' \
                       '"\\help" to to list commands.'
        message += '\n'
        post_message('[Me] ', message, True)

    def do_message(self, line):
        """Sends a message to the server that the other users can see."""
        if self.connect:
            message = 'message ' + line
            self.chat_client.send_message(message)
        else:
            self.no_server()

    def do_listusers(self, line):
        """Requests a list of users fromt the server."""
        if self.connect:
            message = 'username ' + line
            self.chat_client.send_message(message)
        else:
            self.no_server()

    def do_connect(self, line):
        """Connects to the server with the specified address, port and username."""
        if not self.connect:
            try:
                self.chat_client = ChatClient(self.server, self.port, self.username)
            except ConnectionRefusedError:
                message_format = 'ERROR: Connection to {0}:{1} refused. Unable to connect\n'
                message = message_format.format(self.server, self.port)
                post_message('[Me] ', message, True)
            else:
                self.connect = True
                self.receive_thread = ReceiveThread(self, self.chat_client)
                self.receive_thread.start()
        else:
            self.yes_server()

    def do_disconnect(self, line):
        """Disconnects from the given server"""
        if self.connect:
            self.connect = False
            time.sleep(.1)
            self.chat_client.disconnect()
        else:
            self.no_server()

    def do_close(self, line):
        """Disconnects from the server if connected, then shuts down the client."""
        if self.connect:
            self.connect = False
            time.sleep(.1)
            self.chat_client.disconnect()
            return True
        else:
            return True

    def do_server(self, line):
        """Sets the server'a address to the given address."""
        if not self.connect:
            split = line.split()
            self.server = split[0]
        else:
            self.yes_server()

    def do_serverinfo(self, line):
        """Displays the server information to the user."""
        message_format = 'Current server information to {0}:{1} as {2}\n'
        message = message_format.format(self.server, self.port, self.username)
        post_message('[Me] ', message, True)
        if self.connect:
            message = 'You are currently connected to this server.\n'
        else:
            message = 'You are not currently connected to this server.\n'
        post_message('[Me] ', message, True)

    def do_port(self, line):
        """"Changes the port to the given port."""
        if not self.connect:
            split = line.split()
            self.port = int(split[0])
        else:
            self.yes_server()

    def do_whisper(self, line):
        """Sends a message to the given user that only they can see."""
        if self.connect:
            message = 'whisper ' + line
            self.chat_client.send_message(message)
        else:
            self.no_server()

    def do_username(self, line):
        """Changes the username to the given name."""
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
        post_message('', 'Welcome to the chat client.')
        self.do_connect(None)


class ReceiveThread(threading.Thread):
    """Creates a separate thread to check the socket that is connected to the server."""
    def __init__(self, chat_cmd, chat_client):
        threading.Thread.__init__(self)
        self.cmd = chat_cmd
        self.client = chat_client

    def run(self):
        time.sleep(.1)
        while self.cmd.connect:
            message = self.client.receive_message()
            if message :
                self.cmd.connect = False
