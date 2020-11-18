from __future__ import annotations
import random
from itertools import chain

from game.player import Player
from game.utils import circles_collide, Vec, is_outside_box
from game.items import ITEMS, WeaponItem
from game.moving_objects import PathMover
from game.modifiers import CrownModifier, MaskModifier
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
            Vec(**spot): None
            for spot in config.global_config.items
        }
        self.picked_items = {player: [] for player in self.players}
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
        items_not_on_map = list(set(ITEMS) - set(map(type, chain(self.item_spots.values(), self.picked_items.values()))))
        random.shuffle(empty_spots)
        random.shuffle(items_not_on_map)

        for _ in range(min(len(empty_spots), len(items_not_on_map), n)):
            self.item_spots[empty_spots.pop()] = items_not_on_map.pop()()

    def tick(self, commands):
        moves, shots, pick_weapons = self.split_actions(commands)

        active_players = self.chainsaw_logic()

        for move_action in moves:
            move_action.apply()

        for player in self.players:
            player.timeouts()

        self.item_logic(active_players, pick_weapons)

        for item in self.modifiers:
            if isinstance(item, CrownModifier):
                item.tick()

        self.bullets_logic(active_players)
        self.perform_shots(shots)

        self.ticks += 1

    @staticmethod
    def split_actions(commands):
        moves = []
        shots = []
        pick_weapons = []
        for command in commands:
            move, shot, pick_weapon = command
            if move is not None:
                moves.append(move)
            if shot is not None:
                shots.append(shot)
            if pick_weapon is not None:
                pick_weapons.append(pick_weapon)

        return moves, shots, pick_weapons

    def get_active_players(self):
        return [
            player
            for player in self.players
            if player.invulnerability_timer.ready()
        ]

    def chainsaw_logic(self):
        active_players = self.get_active_players()

        for chainsaw in self.chainsaws:
            chainsaw.move()

            for player_index in range(len(active_players) - 1, -1, -1):
                player = active_players[player_index]
                if circles_collide(player.position, chainsaw.position,
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
                              config.global_config.box_width,
                              config.global_config.box_height):
                del self.bullets[bullet_index]
                continue

            masks = [item for item in self.modifiers if isinstance(item, MaskModifier) and item.player == bullet.player]

            for player_index in range(len(active_players) - 1, -1, -1):
                player = active_players[player_index]
                if (bullet.player != player
                        and circles_collide(bullet.position, player.position,
                                            config.global_config.bullet_radius,
                                            config.global_config.player_radius)):

                    bullet.player.score += bullet.player.weapon.hit_score

                    for mask in masks:
                        mask.tick()

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
                if circles_collide(player.position, item_spawn,
                                   config.global_config.player_radius,
                                   config.global_config.item_radius):
                    # item can't be picked up when it collides with multiple players
                    if player_collides is None:
                        player_collides = player
                    else:
                        player_collides = None
                        break

            if player_collides:
                modifier = item.pick(player_collides)
                self.item_spots[item_spawn] = None
                self.picked_items[player_collides].append(item)
                if modifier:
                    self.modifiers.append(modifier)

    def drop_player(self, player):
        player.drop_out(config.global_config.invulnerability_timeout)

        self.modifiers = [
            modifier
            for modifier in self.modifiers
            if not modifier.try_detach_from_player(player)
        ]

        fill_number = len(self.picked_items[player])
        self.picked_items[player] = []
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
                    'speed': player.speed,
                    'position_x': player.position.x, 'position_y': player.position.y,
                    'hit_score': player.weapon.hit_score,
                    'bullet_count': player.weapon.bullet_count,
                    'reload_timeout': player.weapon.reload_timer.ticks,
                    'shot_timeout': player.weapon.shot_timer.ticks,
                    'invulnerability_timeout': player.invulnerability_timer.ticks,
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
            'items': [
                {
                    'id': item.id,
                    'spawn_x': item_spawn.x,
                    'spawn_y': item_spawn.y,
                }
                for item_spawn, item in self.item_spots.items()
                if item is not None
            ],
            'chainsaws': [
                {
                    'position_x': chainsaw.position.x,
                    'position_y': chainsaw.position.y,
                    'target_index': chainsaw.target_index,
                    'target_x': chainsaw.target.x,
                    'target_y': chainsaw.target.y
                }
                for chainsaw in self.chainsaws
            ],
        }
