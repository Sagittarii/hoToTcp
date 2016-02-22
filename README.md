# hoToTcp
Gateway Hangouts to Tcp (using python's hangups library)

This allows to use the python hangups library from other languages, using a TCP connection.

The hoToTcp program acts as a TCP server. The client, written in any language, simply has to connect to the server.


Communication is done through json documents, to ease sharing complex structures, like the users and conversations details, and not only raw text.


# Usage 
Install hangups, and use it a first time to setup an authentication cookie.

Then launch the hoToTcp server, providing the location of this cookie and the port to use (for example 2222):
    ./hoToTcp.py ~/.cache/hangups/refresh_token.txt 2222

Then connect an other app to the chosen port. At the connection, a first Json document is sent by the server with the list of users and opened conversations.
Then at each received message on hangouts, a json document is pushed to the tcp connection, containing details like the conversation id (to be able to reply to the good one), the user that sent it and the timestamp.

To send a message to hangout, send a json document containing the conversation id, and the text to send, to the hoToTcp server.


# Known limitation
This code is still a work in progress, and I am not a professionnal python developper (this is the reason of this project : using hangups from C++ or other languages), so several limitations are know:

If the client disconnect and reconnects, the messages are not correctly directed to this new connection. This has to do with closing properly the protocol object created at each connection, which still tries to get messages from the queues. It will be solved in the near future.

Message segments properties (bold, italic, links, ...) are not used, and will be generated from html markup ("b" "i" and "a" tags).

Images should be handled too.
