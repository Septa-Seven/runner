from __future__ import annotations
from typing import Optional

import random

from game.player import Player
from game.utils import circles_collide, is_outside_box, random_position
from game.items import WEAPON_ITEM_CLASSES, WeaponItem, CrownItem
from game.chainsaw import Chainsaw
from game.modifiers import CrownModifier
from game.weapons import ShotError
import config


class Game:
    def __init__(self):
        self.players = [
            Player(player_spawn.id, player_spawn.position)
            for player_spawn in config.global_config.players.spawns
        ]

        self.bullets = []

        self.chainsaws = [
            Chainsaw(chainsaw.radius, chainsaw.speed, chainsaw.path)
            for chainsaw in config.global_config.chainsaws
        ]

        self.items = {
            spot: random.choice(WEAPON_ITEM_CLASSES)()
            for spot in config.global_config.items.spots
        }
        self.items[config.global_config.items.crown.spot] = CrownItem()
        self.modifiers = []

        self.ticks = 0

    def tick(self, commands):
        move_directions, dashes, shots, pick_weapons = self.split_actions(commands)

        active_players = self.chainsaw_logic()

        for move_directions_action in move_directions:
            move_directions_action.apply()

        for dash_action in dashes:
            dash_action.apply()

        for player in self.players:
            player.timeouts()
            player.move()

        self.item_logic(active_players, pick_weapons)

        self.spawn_item()

        for item in self.modifiers:
            if isinstance(item, CrownModifier):
                item.tick()

        self.bullets_logic(active_players)
        self.perform_shots(shots)

        self.ticks += 1

    @staticmethod
    def split_actions(commands):
        actions = ([], [], [], [])
        for command in commands:
            for i, action in enumerate(command):
                if action is not None:
                    actions[i].append(action)

        return actions

    def get_active_players(self):
        return [
            player for player in self.players if player.invulnerability.is_over()
        ]

    def chainsaw_logic(self) -> list[Player]:
        active_players = self.get_active_players()

        for chainsaw in self.chainsaws:
            chainsaw.move()

            for player_index in range(len(active_players) - 1, -1, -1):
                player = active_players[player_index]
                if circles_collide(player.movement.position, chainsaw.position,
                                   config.global_config.players.radius, chainsaw.radius):
                    self.drop_player(player)
                    del active_players[player_index]

            for bullet_index in range(len(self.bullets) - 1, -1, -1):
                bullet = self.bullets[bullet_index]
                if circles_collide(bullet.position, chainsaw.position,
                                   config.global_config.items.weapons.bullet_radius,
                                   chainsaw.radius):
                    del self.bullets[bullet_index]

        return active_players

    def bullets_logic(self, active_players):
        for bullet_index in range(len(self.bullets) - 1, -1, -1):
            bullet = self.bullets[bullet_index]
            if is_outside_box(bullet.position.x, bullet.position.y,
                              config.global_config.arena.width,
                              config.global_config.arena.height):
                del self.bullets[bullet_index]
                continue

            for player_index in range(len(active_players) - 1, -1, -1):
                player = active_players[player_index]
                if (bullet.player != player
                        and circles_collide(bullet.position, player.movement.position,
                                            config.global_config.items.weapons.bullet_radius,
                                            config.global_config.players.radius)):

                    bullet.player.score += bullet.player.weapon.hit_score

                    del self.bullets[bullet_index]

                    self.drop_player(player)
                    del active_players[player_index]

                    break
            else:
                bullet.move()

        return active_players

    def item_logic(self, active_players, pick_weapons):
        players_trying_pick = [
            pick_weapon.player
            for pick_weapon in pick_weapons
            if pick_weapon.player in active_players
        ]

        for item_position, item in list(self.items.items()):

            if isinstance(item, WeaponItem):
                check_players = players_trying_pick
            else:
                check_players = active_players

            player_collides = None
            for player in check_players:
                if circles_collide(player.movement.position, item_position,
                                   config.global_config.players.radius,
                                   config.global_config.items.radius):
                    # item can't be picked up when it collides with multiple players
                    if player_collides is None:
                        player_collides = player
                    else:
                        player_collides = None
                        break

            if player_collides:
                modifier = player_collides.pick_item(item)
                del self.items[item_position]
                if modifier:
                    self.modifiers.append(modifier)

    def spawn_item(self):
        if self.ticks % config.global_config.items.spawn_period != 0:
            return

        empty_spots = list(set(config.global_config.items.spots).difference(self.items.keys()))
        if not empty_spots:
            return

        spot = random.choice(empty_spots)
        item = random.choice(WEAPON_ITEM_CLASSES)()

        self.items[spot] = item

    def drop_player(self, player):
        if any(isinstance(item, CrownItem) for item in player.items):
            self.items[config.global_config.items.crown.spot] = CrownItem()

        player.drop_out(config.global_config.players.drop_out_invulnerability_timeout)

        self.modifiers = [
            modifier
            for modifier in self.modifiers
            if not modifier.try_detach_from_player(player)
        ]

    def perform_shots(self, shots):
        for shot_action in shots:
            try:
                bullets = shot_action.apply(self.ticks)
            except ShotError:
                continue
            else:
                self.bullets += bullets

    def is_ended(self):
        return self.ticks == config.global_config.restrictions.max_ticks

    def get_player_by_id(self, player_id: int) -> Optional[Player]:
        for player in self.players:
            if player.id == player_id:
                return player

    def get_state(self):
        return {
            'ticks': self.ticks,
            'players': [
                {
                    'id': player.id,
                    'score': player.score,
                    'speed': player.movement.speed,
                    'position_x': player.movement.position.x, 'position_y': player.movement.position.y,
                    'hit_score': player.weapon.hit_score,
                    'bullet_count': player.weapon.bullet_count,
                    'shot_timeout': player.weapon.shot_cooldown.ticks,
                    'invulnerability_timeout': player.invulnerability.ticks,
                    'dash': player.dash.ticks,
                    'dash_cooldown': player.dash_cooldown.ticks,
                    'items': [item.id for item in player.items]
                }
                for player in self.players
            ],
            'bullets': [
                {
                    'player_id': bullet.player.id,
                    'position_x': bullet.position.x, 'position_y': bullet.position.y,
                    'velocity_x': bullet.velocity.x, 'velocity_y': bullet.velocity.y
                }
                for bullet in self.bullets
            ],
            'chainsaws': [
                {
                    'position_x': chainsaw.position.x,
                    'position_y': chainsaw.position.y,
                    'target_index': chainsaw.target_index,
                    'target_x': chainsaw.target.x,
                    'target_y': chainsaw.target.y,
                }
                for chainsaw in self.chainsaws
            ],
            'items': [
                {'id': item.id, 'position_x': item_position.x, 'position_y': item_position.y}
                for item_position, item in self.items.items()
            ]
        }
