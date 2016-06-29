#!/usr/bin/env python3
import select
from .PostMessage import *
from socket import *


class ChatServer:
    def __init__(self, port):
        self.server_sock = socket(AF_INET, SOCK_STREAM)
        self.server_sock.bind(('', port))

        self.server_sock.listen(5)
        self.ACTIVE_SOCKETS = {self.server_sock: 'Server'}
        post_message('>  ', 'Server started on port {0}\n'.format(port))

    def close(self):
        """Disconnects from all connections and closes server."""
        message = 'shutdown'
        for connection in self.ACTIVE_SOCKETS:
            if connection is not self.server_sock:
                send_data(message.encode(), [connection])
            self.disconnect(connection, suppress=True)

    def check_sockets(self):
        """Checks sockets for new messages."""
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
                post_message('>  ', 'Connection Reset\n')
                self.disconnect_message(connection)

    def accept_connection(self, connection):
        """Accepts a new connections and checks if the username is valid."""
        client, address = connection.accept()
        read1, write1, err1 = select.select([client], [], [], .1)
        if client in read1:
            username = client.recv(2 ** 16).decode().strip()
            if username not in self.ACTIVE_SOCKETS.values():
                self.ACTIVE_SOCKETS[client] = username
                post_message('>  ', 'Connection at {0} as {1}\n'.format(address, username))
                message = 'connection {0}'.format(username)
                self.server_broadcast(message, skip=[client])
            else:
                message_format = 'Connection at {0} as {1}.\n'
                message_format += 'Username already taken, disconnecting\n'
                post_message('>  ', message_format.format(address, username))
                data = generate_message_data('name_taken ' + username, 'error')
                send_data(data, [client])
                client.close()
        else:
            client.close()
            post_message('>  ', 'Attempted Connection at {0}\n'.format(address))
            post_message('>  ', 'No username, disconnecting.\n')

    def read_message(self, connection):
        """Reads and processes a message send by a user."""
        data = connection.recv(2 ** 16)
        if data:
            name = self.ACTIVE_SOCKETS[connection]
            message = data.decode().strip()
            tag, message = split_message(message)
            post_message('>  ', '[{0}] <{1}> {2}\n'.format(name, tag, message))
                
            if tag == 'message':
                self.user_message(message, connection)
            elif tag == 'username':
                self.username_request(connection)
            elif tag == 'whisper':
                username, message = split_message(message)
                if message is None or username is None:
                    return None
                recipient = [k for k, v in self.ACTIVE_SOCKETS.items() if v == username]
                if len(recipient) == 1:
                    data = generate_message_data(message, 'whisper', name)
                    send_data(data, recipient)
                else:
                    message_format = 'no_name_whisper {0}\n'
                    message = message_format.format(username)
                    data = generate_message_data(message, 'error')
                    post_message('>  ', message)
                    send_data(data, connection)
        else:
            self.disconnect(connection)

    def disconnect(self, connection, suppress=False):
        """Disconnects a user from the server."""
        connection.close()
        if not suppress:
            self.disconnect_message(connection)

    def disconnect_message(self, connection):
        """Sends a message that a user disconnected to the remaining users."""
        if connection in self.ACTIVE_SOCKETS:
            name = self.ACTIVE_SOCKETS.pop(connection)
            message = 'disconnection {0}\n'.format(name)
            post_message('>  ', message)
            self.server_broadcast(message)

    def server_broadcast(self, message, skip=list()):
        """Broadcasts a message from the server to all users."""
        data = generate_message_data(message, 'server_broadcast')
        skip.append(self.server_sock)
        recipients = [x for x in self.ACTIVE_SOCKETS if x not in skip]
        send_data(data, recipients)

    def user_message(self, message, sender_sock):
        """Sends a message from a user to the other users."""
        name = self.ACTIVE_SOCKETS[sender_sock]
        skip = [self.server_sock, sender_sock]
        data = generate_message_data(message, 'user_message', name)
        recipients = [x for x in self.ACTIVE_SOCKETS if x not in skip]
        send_data(data, recipients)

    def username_request(self, sender_sock):
        """Sends a list of usernames to the requesting user."""
        user_list = list(self.ACTIVE_SOCKETS.values())
        user_list.remove('Server')
        user_list_len = len(user_list)
        user_list = user_list[:10]
        len_diff = user_list_len - len(user_list)
        message = ' '.join(user_list)
        data = generate_message_data(message, 'username', None, len_diff)
        send_data(data, [sender_sock])


def split_message(message):
    """Splits a message into its tag and the body of the message"""
    split = message.strip().split(sep=None, maxsplit=1)
    if len(split) == 0:
        return '', ''
    elif len(split) == 1:
        return split[0], ''
    else:
        return split[0], split[1]


def send_data(data, recipients):
    """Sends data to a the given recipients."""
    if data is not None:
        try:
            for connection in recipients:
                connection.send(data)
        except TypeError:
            recipients.send(data)


def generate_message_data(message, message_type, sender=None, *args):
    """Generates and encodes the message data with """
    if message_type == 'user_message':
        return 'message {0} {1}'.format(sender, message).encode()
    elif message_type == 'server_broadcast':
        return '{0}'.format(message).encode()
    elif message_type == 'username':
        return 'username {0} {1}'.format(args[0], message).encode()
    elif message_type == 'error':
        return 'error {0}'.format(message).encode()
    elif message_type == 'whisper':
        return 'whisper {0} {1}'.format(sender, message).encode()
