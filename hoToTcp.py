#!/usr/bin/python3


import asyncio
import hangups
import sys
import json
from hangups.conversation import ConversationList, build_user_conversation_list


class TcpServer(asyncio.Protocol):
    def connection_made(self, transport):
        """
        Called when a connection is made.
        The argument is the transport representing the pipe connection.
        To receive data, wait for data_received() calls.
        When the connection is closed, connection_lost() is called.
        """
        print("Connection received!", self, dir(self))
        self.transport = transport

        asyncio.async(self._send_messages())  # Or asyncio.ensure_future if using 3.4.3+
        print("## Loop finished in connection_made")

    @asyncio.coroutine
    def _send_messages(self):
        """ Send messages to the server as they become available. """
        print("## TCP receive loop Ready!")
        while True:
            data = yield from queueHoToTcp.get()
            self.transport.write(data.encode('utf-8'))
            print('TCP Message sent: {!r}'.format(data))

    def data_received(self, raw):
        """
        Called when some data is received.
        The argument is a bytes object.
        """
        print("TCP received data :", raw)
        data = json.loads(raw.decode('utf-8'))
        asyncio.async(self.send_message_to_Ho(data))

    @asyncio.coroutine
    def send_message_to_Ho(self, data):
        yield from queueTcpToHo.put(data)

    @asyncio.coroutine
    def connection_lost(self, exc):
        """
        Called when the connection is lost or closed.
        The argument is an exception object or None (the latter
        meaning a regular EOF is received or the connection was
        aborted or closed).
        """
        print("TCP Connection lost! Closing server...")
        #server.close()


class HoClient():
    def __init__(self, loop, inQueue, outQueue, cookiePath):
        self.loop = loop
        self.inQueue = inQueue
        self.outQueue = outQueue

        cookies = hangups.auth.get_auth_stdin(cookiePath)
        self.client = hangups.Client(cookies)
        self.client.on_connect.add_observer(lambda: asyncio.async(self.on_connect()))

        asyncio.async(self.client.connect())

    @asyncio.coroutine
    def on_connect(self):
        """Handle connecting for the first time (callback)"""
        print('Ho Connected')

        user_list, conv_list = (
            yield from hangups.build_user_conversation_list(self.client)
        )

        self.userIds = []
        for u in user_list.get_all():
            print(u.id_, u.first_name, u.full_name, u.photo_url, u.emails)
            self.userIds.append({"id": u.id_.chat_id, "first_name": u.first_name, "full_name": u.full_name})            


        self.convIds = []
        for c in conv_list.get_all():
            print(c.users, dir(c.users))
            print(c.id_, c.name, [x.id_.chat_id for x in c.users])
            print(c.users, dir(c.users))
            print(c.id_, c.name, [x.id_.chat_id for x in c.users])
            self.convIds.append({"id":c.id_, "name":c.name, "users": [x.id_.chat_id for x in c.users]})
        print("Conversation list :", self.convIds)

        conv_list.on_event.add_observer(self.on_event)

        asyncio.async(self._send_messages())  # Or asyncio.ensure_future if using 3.4.3+

        yield from self.outQueue.put(json.dumps({"conversations": self.convIds, "users": self.userIds}))
        print("## Ho Connection handling done")

    @asyncio.coroutine
    def _send_messages(self):
        """ Send messages to the server as they become available. """
        print("## HO receive loop Ready!")
        while True:
            data = yield from self.inQueue.get()
            print('HO Message sent: {!r}'.format(data))
            asyncio.async(self.send_message(data["conversation"], data["text"]))
        print("## HO receive loop Finished")

    @asyncio.coroutine
    def send_message(self, convId, data):
        print("send message :", data)
        request = hangups.hangouts_pb2.SendChatMessageRequest(
            request_header=self.client.get_request_header(),
            event_request_header=hangups.hangouts_pb2.EventRequestHeader(
                conversation_id=hangups.hangouts_pb2.ConversationId(
                    id=convId
                ),
                client_generated_id=self.client.get_client_generated_id(),
            ),
            message_content=hangups.hangouts_pb2.MessageContent(
                segment=[hangups.ChatMessageSegment(data).serialize()],
            ),
        )
        yield from self.client.send_chat_message(request)


    @asyncio.coroutine
    def on_status_changes(self):
        print("on_status_changes", self)


    @asyncio.coroutine
    def on_event(self, conv_event):
        print("on_event", conv_event, dir(conv_event))
        if isinstance(conv_event, hangups.ChatMessageEvent):
            print("## On Event. Pushing data to queue HoToTcp")
            yield from self.outQueue.put(json.dumps({"conversation": conv_event.conversation_id, "timestamp": conv_event.timestamp.timestamp(), "user": conv_event.user_id.chat_id, "text": conv_event.text}))
            print("## On Event. data pushed to queue HoToTcp")


    @asyncio.coroutine
    def _on_status_changes(self, state_update):
        if state_update.HasField('conversation'):
            print("status changes : conversation")

        if state_update.watermark_notification is not None:
            print("watermark notification")


#def main(argv):
argv=sys.argv
if (len(argv) != 3):
    print("Usage : hoToTcp /path/to/.cache/hangups/refresh_token.txt port")
    sys.exit(-1);
#    return -1;


print("Starting hoToTcp gateway...")

loop = asyncio.get_event_loop()

print("Creating Messages Queues")
queueHoToTcp = asyncio.Queue(maxsize=0, loop=loop)
queueTcpToHo = asyncio.Queue(maxsize=0, loop=loop)
print("Queues created")

print("Creating Hangups client")
ho = HoClient(loop, queueTcpToHo, queueHoToTcp, argv[1])
print("Hangups client created")

print("Creating TCP Server")
server = loop.run_until_complete(loop.create_server(TcpServer, 'localhost', argv[2]))
print("Server created")

print("hoToTcp gateway Started !")
print("****-----------------****")
loop.run_forever()
print("Loop finished, exiting...")
exit(0)
#return 0


#if __name__ == '__main__':
#    main(sys.argv)
#    sys.exit(main(sys.argv))

 