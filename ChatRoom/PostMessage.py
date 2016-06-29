import sys
import readline


def post_message(message, from_cmd=False):
    """Post a message to the commandline without interfering with the typed commands"""
    temp = readline.get_line_buffer()
    sys.stdout.write('\r' + ' ' * (len(temp) + 5) + '\r')
    sys.stdout.write(message)

    if not from_cmd:
        sys.stdout.write('[Me] ' + temp)
    sys.stdout.flush()