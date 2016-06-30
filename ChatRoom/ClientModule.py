#!/usr/bin/env python3
import select
from .PostMessage import *
from socket import *  # import *, but we'll avoid name conflict


class ChatClient:
    def __init__(self, server, port, username):
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.sock.connect((server, port))
        self.sock.send(username.encode())
        self.username = username

    # def check(self):
    #     """Checks the connection to the server for new messages."""
    #     to_read = list(sys.stdin)
    #     read, write, err = select.select(to_read, [], [], 0)
    #     if sys.stdin in read:
    #         return sys.stdin.readline
    #     else:
    #         self.receive_message()
    #         return ''

    def send_message(self, message):
        """Sends a message to the server."""
        message_len = self.sock.send(message.encode())

        if message_len != len(message):
            print("Failed to send complete message")

    def receive_message(self):
        """Checks the connection with the server and receives a message if available."""
        read, write, err = select.select([self.sock], [], [], 0)
        if self.sock in read:
            message = self.sock.recv(2 ** 16).strip().decode()
            if message:
                tag, message = split_message(message)
                if tag == 'no_message':
                    pass
                elif tag == 'message':
                    username, message = split_message(message)
                    message_format = '[{0}] said: {1}\n'
                    message = message_format.format(username, message)
                    post_message('[Me] ', message)
                elif tag == 'username':
                    self.username_list(message)
                elif tag == 'disconnection':
                    message_format = '{0} has disconnected.\n'
                    message = message_format.format(message)
                    post_message('[Me] ', message)
                elif tag == 'connection':
                    message_format = '{0} has connected.\n'
                    message = message_format.format(message)
                    post_message('[Me] ', message)
                elif tag == 'error':
                    self.error_message(message)
                elif tag == 'shutdown':

                    post_message('[Me] ', 'Server has shutdown.\n')
                    self.disconnect()
                    return'disconnect'
                elif tag == 'whisper':
                    username, message = split_message(message)
                    message_format = '[{0}] whispers: {1}\n'
                    message = message_format.format(username, message)
                    post_message('[Me] ', message)
        else:
            self.disconnect()
            post_message('[Me] ', 'Lost connection to server.\n')
            return True

    def username_list(self, message):
        """"Displays the username list sent from the server to the user."""
        extras, usernames = split_message(message)
        extras = int(extras)
        usernames = usernames.split()
        if extras == 0:
            if len(usernames) == 1:
                message = usernames
                message_format = 'You, {0}, are the only user connected.\n'
            elif len(usernames) == 2:
                usernames.remove(self.username)
                message = usernames[0]
                message_format = 'You and {0} are the only users connected.\n'
            else:
                message = ', '.join(usernames[:-1])
                message_format = 'The connected users are {0}, and {1}.\n'
            message = message_format.format(message, usernames[-1])
        else:
            if len(usernames) == 0:
                message_format = 'There are {0} users currently connected'
                message = message_format.format(extras)
            else:
                message = ', '.join(usernames)
                message_format = 'The connected users are {0}and {1} more.\n'
                message = message_format.format(message, extras)
        post_message('[Me] ', message)

    def error_message(self, message):
        """"Displays the error message sent from the server to the user."""
        tag, message = split_message(message)
        if tag == 'name_taken':
            self.disconnect()
            message_format = 'ERROR: Username {0} already taken, use ' \
                             '"\\username" to choose a new one.\n'
            message = message_format.format(self.username)
            post_message('[Me] ', message)
            return 'disconnect'
        elif tag == 'no_name_whisper':
            message_format = 'ERROR: Unable to whisper, user {0} not found.\n'
            message = message_format.format(message)
            post_message('[Me] ', message)

    def disconnect(self):
        """Disconnects from the server."""
        self.sock.close()
        self.sock = None


def split_message(message):
    """Splits a message into its tag and the body of the message"""
    split = message.strip().split(sep=None, maxsplit=1)
    if len(split) < 2:
        return split[0], ''
    else:
        return split[0], split[1]
