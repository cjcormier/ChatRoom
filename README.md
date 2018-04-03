# ChatRoom
ChatRoom

This is a basic chatroom, implemented in python3.6, for CS 3516 Computer Networks at WPI. This project has two applications, 
the client and the server. Both applications have command line arguments that can be access via the -h descriptor. Each application
has a ui and module portion. The UI portion handles updating and receiving input from the terminal while the module handles 
sending and receiving messages from the connection. The UI is implemented using the 
[cmd library](https://docs.python.org/2/library/cmd.html) for python, while the module uses the 
[socket library](https://docs.python.org/3/library/socket.html). After starting the program, type help (or \help for the client) to 
display help dialog.

This project requires readline, if you are on windows please install (pyreadline)[https://pypi.python.org/pypi/pyreadline], 
if you are on OSX install [gnureadline](https://pypi.python.org/pypi/gnureadline).
