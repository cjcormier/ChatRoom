#!/usr/bin/env python3
import cmd
import readline
import select
import sys
import threading
import time
from socket import *


class ChatServerCMD(cmd.Cmd):
    intro = 'Welcome to the chat client.'
    prompt = '> '
    file = None
    done = True

    def __init__(self, chat_server):
        cmd.Cmd.__init__(self)
        self.chat_server = chat_server
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
    def __init__(self, server_cmd, chat_server):
        threading.Thread.__init__(self)
        self.server = chat_server
        self.server_cmd = server_cmd

    def run(self):
        first = True
        while not self.server_cmd.done:
            temp = readline.get_line_buffer()
            sys.stdout.write('\r' + ' ' * (len(temp) + 2) + '\r')
            self.server.check_sockets()
            if first:
                first = False
            else:
                sys.stdout.write('> ' + temp)
            sys.stdout.flush()
            time.sleep(.1)


class ChatServer:
    def __init__(self, port):
        self.server_sock = socket(AF_INET, SOCK_STREAM)
        self.server_sock.bind(('', port))

        self.server_sock.listen(5)

        self.ACTIVE_SOCKETS = {self.server_sock: 'Server'}
        print('Server started on port {0}'.format(port))

    def close(self):
        message = 'shutdown'
        for connection in self.ACTIVE_SOCKETS:
            if connection is not self.server_sock:
                send_data(message.encode(), [connection])
            self.disconnect(connection, suppress=True)

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
        read1, write1, err1 = select.select([client], [], [], .1)
        if client in read1:
            username = client.recv(2 ** 16).decode().strip()
            if username not in self.ACTIVE_SOCKETS.values():
                self.ACTIVE_SOCKETS[client] = username
                print('Connection at {0} as {1}'.format(address, username))
                message = 'connection {0}'.format(username)
                self.server_broadcast(message, skip=[client])
            else:
                message_format = 'Connection at {0} as {1}.\n'
                message_format += 'Username already taken, disconnecting'
                print(message_format.format(address, username))
                data = generate_message_data('name_taken ' + username, 'error')
                send_data(data, [client])
                client.close()
        else:
            client.close()
            print('Attempted Connection at {0}'.format(address))
            print('No username, disconnecting.')

    def read_message(self, connection):
        data = connection.recv(2 ** 16)
        if data:
            name = self.ACTIVE_SOCKETS[connection]
            message = data.decode().strip()
            tag, message = split_message(message)
            print('[{0}] <{1}> {2}'.format(name, tag, message))
                
            if tag == 'message':
                self.user_message(message, connection)
            elif tag == 'username':
                self.username_request(connection)
            elif tag == 'whisper':
                username, message = split_message(message)
                recipient = [k for k, v in self.ACTIVE_SOCKETS.items() if v == username]
                if len(recipient) == 1:
                    data = generate_message_data(message, 'whisper', name)
                    send_data(data, recipient)
                else:
                    message = 'Unable to whisper, user {0} not found'
                    data = generate_message_data(message, 'error')
                    send_data(data, connection)
        else:
            self.disconnect(connection)

    def disconnect(self, connection, suppress=False):
        connection.close()
        if not suppress:
            self.disconnect_message(connection)

    def disconnect_message(self, connection):
        if connection in self.ACTIVE_SOCKETS:
            name = self.ACTIVE_SOCKETS.pop(connection)
            message = 'disconnection {0}'.format(name)
            print(message)
            self.server_broadcast(message)

    def server_broadcast(self, message, skip=list()):
        data = generate_message_data(message, 'server_broadcast')
        skip.append(self.server_sock)
        recipients = [x for x in self.ACTIVE_SOCKETS if x not in skip]
        send_data(data, recipients)

    def user_message(self, message, sender_sock):
        name = self.ACTIVE_SOCKETS[sender_sock]
        skip = [self.server_sock, sender_sock]
        data = generate_message_data(message, 'user_message', name)
        recipients = [x for x in self.ACTIVE_SOCKETS if x not in skip]
        send_data(data, recipients)

    def username_request(self, sender_sock):
        user_list = list(self.ACTIVE_SOCKETS.values())
        user_list.remove('Server')
        user_list_len = len(user_list)
        user_list = user_list[:10]
        len_diff = user_list_len - len(user_list)
        message = ' '.join(user_list)
        data = generate_message_data(message, 'username', None, len_diff)
        send_data(data, [sender_sock])


def split_message(message):
    split = message.strip().split(sep=None, maxsplit=1)
    if len(split) < 2:
        return split[0], ''
    else:
        return split[0], split[1]


def send_data(data, recipients):
    if data is not None:
        for connection in recipients:
            connection.send(data)


def generate_message_data(message, message_type, sender=None, *args):
    if message_type == 'user_message':
        return 'message {0} {1}'.format(sender, message).encode()
    elif message_type == 'server_broadcast':
        return '{0}'.format(message).encode()
    elif message_type == 'username':
        return 'username {0} {1}'.format(args[0], message).encode()
    elif message_type == 'error':
        return 'error {0}'.format(message).encode()
    elif message_type == 'whisper':
        return 'whisper {0} {1}'.format(sender, message)
