from typing import List

import asyncio
import json
import random

from game.game import Game
from clients import Client
import config
from parsing import parse_command


class GameLoop:
    def __init__(self, game: Game, clients: List[Client]):
        self.game = game
        random.shuffle(clients)
        self.clients = dict(enumerate(clients))
        self.keep_work = True

    def stop(self):
        self.keep_work = False

    async def play(self):
        # send game config
        config_json = config.global_config.json()

        messages = []
        for client_id in self.clients:
            config_json['my_id'] = client_id
            messages.append(self.send_message_wrapper(client_id, json.dumps(config_json)))

        await self.send_messages(messages)

        # game
        while not self.game.is_ended() and self.clients and self.keep_work:
            # send game state
            state = json.dumps(self.game.get_state())
            await self.send_messages([self.send_message_wrapper(client_id, state) for client_id in self.clients])

            commands = await self.get_commands()

            parsed_commands = []
            for client_id, command in commands:
                if command is None:
                    continue

                parsed_command = parse_command(self.game, client_id, command)
                parsed_commands.append(parsed_command)

            self.game.tick(parsed_commands)

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
            return await asyncio.wait_for(self.clients[client_id].get_command(),
                                          timeout=config.global_config.execution_timeout)
        except:
            self.disconnect_client(client_id)

    async def send_message_wrapper(self, client_id, msg):
        # send message but if it fails disconnect client
        try:
            await asyncio.wait_for(self.clients[client_id].send_message(msg),
                                   timeout=config.global_config.response_timeout)
        except Exception:
            self.disconnect_client(client_id)

    async def send_messages(self, send_fs):
        if send_fs:
            await asyncio.wait(send_fs)

    def disconnect_client(self, client_id):
        self.clients.pop(client_id).disconnect()
