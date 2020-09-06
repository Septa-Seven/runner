import asyncio
import json

from parsing import parse_command

RESPONSE_TIMEOUT = 2.0
EXECUTION_TIMEOUT = 5.0
MAX_TICKS = 100


class GameLoop:
    def __init__(self, game, clients):
        self.game = game
        self.clients = dict(enumerate(clients))

    async def play(self):
        # send game config
        config_json = self.game.config.json()

        messages = []
        for client_id in self.clients:
            config_json['my_id'] = client_id
            messages.append(self.send_message_wrapper(client_id, json.dumps(config_json)))

        await self.send_messages(messages)

        # game
        while not self.game.is_ended() and self.clients:
            # send game state
            state = json.dumps(self.game.get_state())
            await self.send_messages([self.send_message_wrapper(client_id, state) for client_id in self.clients])

            commands = await self.get_commands()

            client_actions = {}
            for client_id, command in commands:
                if command is None:
                    continue

                actions = parse_command(self.game, client_id, command)

                if actions:
                    client_actions[client_id] = actions

            self.game.tick(client_actions)

        # self.game.save_log('result.json')

    async def get_commands(self):
        client_ids = list(self.clients.keys())
        commands = await asyncio.gather(*(self.get_command_wrapper(client_id) for client_id in client_ids))
        client_commands = [
            (client_id, command)
            for client_id, command in zip(client_ids, commands)
            if command is not None
        ]
        return client_commands

    async def get_command_wrapper(self, client_id):
        # TODO don't know about execution time
        # requests command but if it fails disconnects client
        try:
            return await asyncio.wait_for(self.clients[client_id].get_command(), timeout=EXECUTION_TIMEOUT)
        except:
            self.disconnect_client(client_id)

    async def send_message_wrapper(self, client_id, msg):
        # send message but if it fails disconnect client
        try:
            await asyncio.wait_for(self.clients[client_id].send_message(msg), timeout=RESPONSE_TIMEOUT)
        except:
            self.disconnect_client(client_id)

    async def send_messages(self, send_fs):
        if send_fs:
            await asyncio.wait(send_fs)

    def disconnect_client(self, client_id):
        self.clients.pop(client_id).disconnect()
