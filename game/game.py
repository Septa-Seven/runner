from __future__ import annotations

import random
from itertools import chain

from game.player import Player
from game.utils import circles_collide, Vec, is_outside_box
from game.items import SPOT_ITEMS, WeaponItem
from game.moving_objects import PathMover
from game.modifiers import CrownModifier
from exceptions import ShotError
import config


class Game:
    def __init__(self):
        self.players = [
            Player(player['id'], Vec(player['x'], player['y']))
            for player in config.global_config.players
        ]

        self.bullets = []

        self.item_spots = {
            Vec(**spot): None for spot in config.global_config.items
        }
        self.fill_item_spots(len(self.item_spots))

        self.chainsaws = [
            PathMover(config.global_config.chainsaw_speed,
                      [Vec(**point) for point in chainsaw_path])
            for chainsaw_path in config.global_config.chainsaws
        ]

        self.modifiers = []

        self.ticks = 0

    def fill_item_spots(self, n=1):
        if n <= 0:
            return

        empty_spots = [item_spot for item_spot, item in self.item_spots.items() if item is None]
        items_not_on_map = list(
            SPOT_ITEMS - set(map(type, chain(
                self.item_spots.values(),
                chain.from_iterable(player.items for player in self.players)
            )))
        )
        random.shuffle(empty_spots)
        random.shuffle(items_not_on_map)

        for _ in range(min(len(empty_spots), len(items_not_on_map), n)):
            self.item_spots[empty_spots.pop()] = items_not_on_map.pop()()

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

    def chainsaw_logic(self):
        active_players = self.get_active_players()

        for chainsaw in self.chainsaws:
            chainsaw.move()

            for player_index in range(len(active_players) - 1, -1, -1):
                player = active_players[player_index]
                if circles_collide(player.movement.position, chainsaw.position,
                                   config.global_config.player_radius,
                                   config.global_config.chainsaw_radius):
                    self.drop_player(player)
                    del active_players[player_index]

            for bullet_index in range(len(self.bullets) - 1, -1, -1):
                bullet = self.bullets[bullet_index]
                if circles_collide(bullet.position, chainsaw.position,
                                   config.global_config.bullet_radius,
                                   config.global_config.chainsaw_radius):
                    del self.bullets[bullet_index]

        return active_players

    def bullets_logic(self, active_players):
        for bullet_index in range(len(self.bullets) - 1, -1, -1):
            bullet = self.bullets[bullet_index]
            if is_outside_box(bullet.position.x, bullet.position.y,
                              config.global_config.arena_width,
                              config.global_config.arena_height):
                del self.bullets[bullet_index]
                continue

            for player_index in range(len(active_players) - 1, -1, -1):
                player = active_players[player_index]
                if (bullet.player != player
                        and circles_collide(bullet.position, player.movement.position,
                                            config.global_config.bullet_radius,
                                            config.global_config.player_radius)):

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

        for item_spawn, item in self.item_spots.items():
            if item is None:
                continue

            if isinstance(item, WeaponItem):
                check_players = players_trying_pick
            else:
                check_players = active_players

            player_collides = None
            for player in check_players:
                if circles_collide(player.movement.position, item_spawn,
                                   config.global_config.player_radius,
                                   config.global_config.item_radius):
                    # item can't be picked up when it collides with multiple players
                    if player_collides is None:
                        player_collides = player
                    else:
                        player_collides = None
                        break

            if player_collides:
                modifier = player_collides.pick_item(item)
                self.item_spots[item_spawn] = None
                if modifier:
                    self.modifiers.append(modifier)

    def drop_player(self, player):
        fill_number = len(player.items)

        player.drop_out(config.global_config.drop_out_invulnerability_timeout)

        self.modifiers = [
            modifier
            for modifier in self.modifiers
            if not modifier.try_detach_from_player(player)
        ]

        self.fill_item_spots(fill_number)

    def perform_shots(self, shots):
        for shot_action in shots:
            try:
                bullets = shot_action.apply(self.ticks)
            except ShotError:
                continue
            else:
                self.bullets += bullets

    def is_ended(self):
        return self.ticks == config.global_config.max_ticks

    def get_player_by_id(self, player_id):
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
                    'reload_timeout': player.weapon.reload_cooldown.ticks,
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
            'item_spots': [
                {
                    'id': item.id,
                    'spot_x': item_spot.x,
                    'spot_y': item_spot.y,
                }
                for item_spot, item in self.item_spots.items()
                if item is not None
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
            # 'modifiers': [
            #     modifier.player.id
            #     for modifier in self.modifiers
            # ]
        }
