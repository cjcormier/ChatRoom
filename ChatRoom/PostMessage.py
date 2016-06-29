import sys
import readline


def post_message(prompt, message, from_cmd=False):
    """Post a message to the commandline without interfering with the typed commands"""
    temp = readline.get_line_buffer()
    sys.stdout.write('\r' + ' ' * (len(temp) + len(prompt)) + '\r')
    sys.stdout.write(message)
    sys.stdout.write(prompt + temp)
    sys.stdout.flush()
