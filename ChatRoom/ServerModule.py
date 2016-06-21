#!/usr/bin/env python3
import cmd
import readline
import select
import sys
import threading
from socket import *


class ChatServerCMD(cmd.Cmd):
    intro = 'Welcome to the chat client.'
    prompt = '> '
    file = None
    done = True

    def __init__(self, chat_server):
        cmd.Cmd.__init__(self)
        self.chat_server = chat_server
        self.receiveThread = CheckSocketsThread(self, self.chat_server)

    def preloop(self):
        self.done = False
        self.receiveThread.run()

    def postloop(self):
        self.done = True


class CheckSocketsThread(threading.Thread):
    def __init__(self, server_cmd, chat_server):
        threading.Thread.__init__(self)
        self.server = chat_server
        self.server_cmd = server_cmd

    def run(self):
        while not self.server_cmd.done:
            temp = readline.get_line_buffer()
            sys.stdout.write('\r'+' '*(len(temp)+2)+'\r')
            self.server.check_sockets()
            sys.stdout.write(temp)
            sys.stdout.flush()


class ChatServer:
    def __init__(self, port):
        self.server_sock = socket(AF_INET, SOCK_STREAM)
        self.server_sock.bind(('', port))

        self.server_sock.listen(5)

        self.ACTIVE_SOCKETS = {self.server_sock: 'Server'}
        print('Server started on port {0}'.format(port))

    def check_sockets(self):
        to_read = list(self.ACTIVE_SOCKETS)
        read, write, err = select.select(to_read, [], [], 0)
        for connection in read:
            if connection is sys.stdin:
                continue
            try:
                if connection is self.server_sock:
                    self.accept_connection(connection)
                else:
                    self.read_message(connection)
            except ConnectionResetError:
                print('Connection Reset')
                self.disconnect_message(connection)

    def accept_connection(self, connection):
        client, address = connection.accept()
        read1, write1, err1 = select.select([client], [], [], 0)
        if client in read1:
            username = client.recv(2 ** 16).decode().strip()
            self.ACTIVE_SOCKETS[client] = username
            print('Connection at {0} as {1}'.format(address, username))
            message = 'User, {0}, has connected'.format(username)
            self.server_broadcast(message, skip=[client])
        else:
            client.close()
            print('Attempted Connection at {0}'.format(address))
            print('No username, disconnecting.')

    def read_message(self, connection):
        data = connection.recv(2 ** 16)
        if data:
            message = data.decode().strip()
            name = self.ACTIVE_SOCKETS[connection]
            print('[{0}] {1}'.format(name, message))
            self.user_broadcast(data.decode(), connection)
        else:
            self.disconnect(connection)

    def disconnect(self, connection):
        connection.close()
        self.disconnect_message(connection)

    def disconnect_message(self, connection):
        if connection in self.ACTIVE_SOCKETS:
            name = self.ACTIVE_SOCKETS.pop(connection)
            message = '{} has disconnected'.format(name)
            print(message)
            self.server_broadcast(message)

    def server_broadcast(self, message, skip=list()):
        data = generate_message_data(message, 'server_broadcast')
        skip.append(self.server_sock)
        recipients = [x for x in self.ACTIVE_SOCKETS if x not in skip]
        send_data(data, recipients)

    def user_broadcast(self, message, sender_sock):
        data = generate_message_data(message, 'user_broadcast', self.ACTIVE_SOCKETS[sender_sock])
        recipients = [x for x in self.ACTIVE_SOCKETS if x not in [self.server_sock, sender_sock]]
        send_data(data, recipients)


def send_data(data, recipients):
    print(recipients)
    if data is not None:
        for connection in recipients:
            connection.send(data)


def generate_message_data(message, message_type, sender=None):
    if message_type == 'user_broadcast':
        return '[{0}] {1}\n'.format(sender, message).encode()
    elif message_type == 'server_broadcast':
        return '{0}\n'.format(message).encode()
