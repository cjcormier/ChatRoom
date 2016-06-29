#!/usr/bin/env python3
import threading
import time
import cmd
from .ServerModule import *


class ChatServerCMD(cmd.Cmd):
    intro = 'Welcome to the chat client.'
    prompt = '> '
    file = None
    done = True

    def __init__(self, port):
        cmd.Cmd.__init__(self)
        self.chat_server = ChatServer(port)
        self.receive_thread = CheckSocketsThread(self, self.chat_server)

    def do_close(self, line):
        self.done = True
        print('Closing Server')
        self.chat_server.close()
        return True

    def preloop(self):
        self.done = False
        self.receive_thread.start()


class CheckSocketsThread(threading.Thread):
    """Creates a separate thread to check the various sockets connected to the server."""
    def __init__(self, server_cmd, chat_server):
        threading.Thread.__init__(self)
        self.server = chat_server
        self.server_cmd = server_cmd

    def run(self):
        time.sleep(.1)
        while not self.server_cmd.done:
            self.server.check_sockets()
