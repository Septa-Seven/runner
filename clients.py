import json


EXECUTION_TIMEOUT = 10.0


class Client:
    async def connect(self):
        raise NotImplemented

    async def send_message(self, msg):
        raise NotImplemented

    async def get_command(self):
        raise NotImplemented

    def disconnect(self):
        raise NotImplemented


class ProcessClient(Client):
    def __init__(self, process):
        self.process = process

    async def send_message(self, msg):
        self.process.stdin.write((msg+'\n').encode())
        await self.process.stdin.drain()

    async def get_command(self):
        command = await self.process.stdout.readline()
        return json.loads(command)

    def disconnect(self):
        # there are cases when process terminates before server command to disconnect
        try:
            self.process.terminate()
        except ProcessLookupError:
            pass


class TCPClient(Client):
    def __init__(self, reader, writer):
        self.reader = reader
        self.writer = writer

    async def send_message(self, msg):
        msg_bytes = (msg+'\n').encode()
        self.writer.write(msg_bytes)

    async def get_command(self):
        command = await self.reader.readline()
        return json.loads(command.decode())

    def disconnect(self):
        self.writer.close()
