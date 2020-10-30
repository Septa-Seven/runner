from __future__ import annotations
import random

from game.player import Player
from game.utils import circles_collide, Vec, is_outside_box
from game.items import ITEMS, WeaponItem
from game.modifiers import CrownModifier, MaskModifier
from exceptions import ShotError
import config


class Game:
    def __init__(self):
        self.players = [
            Player(player['id'], Vec(player['position_x'], player['position_y']))
            for player in config.global_config.players
        ]

        self.bullets = []

        self.item_spots = {
            Vec(spawn['spawn_x'], spawn['spawn_y']): None
            for spawn in config.global_config.items
        }
        self.fill_item_spots(len(self.item_spots))

        self.modifiers = []

        self.ticks = 0

    def fill_item_spots(self, n=1):
        if n <= 0:
            return

        empty_spots = [item_spot for item_spot, item in self.item_spots.items() if item is None]
        items_not_on_map = list(set(ITEMS) - set(map(type, self.item_spots.values())))
        random.shuffle(empty_spots)
        random.shuffle(items_not_on_map)

        for _ in range(min(len(empty_spots), len(items_not_on_map), n)):
            self.item_spots[empty_spots.pop()] = items_not_on_map.pop()()

    def tick(self, commands):
        moves, shots, pick_weapons = self.split_actions(commands)

        for move_action in moves:
            move_action.apply()

        for player in self.players:
            player.timeouts()

        # check item collisions
        players_trying_pick = tuple(pick_weapon.player for pick_weapon in pick_weapons)

        for item_spawn, item in self.item_spots.items():
            if item is None:
                continue

            if isinstance(item, WeaponItem):
                check_players = players_trying_pick
            else:
                check_players = self.players

            player_collides = None
            for player in check_players:
                if (player.invulnerability_timer.ready()
                        and circles_collide(player.position, item_spawn,
                                            config.global_config.player_radius,
                                            config.global_config.item_radius)):
                    # item can't be picked up when it collides with multiple players
                    if player_collides is None:
                        player_collides = player
                    else:
                        player_collides = None
                        break

            if player_collides:
                modifier = item.pick(player_collides)
                self.item_spots[item_spawn] = None
                if modifier:
                    self.modifiers.append(modifier)

        for item in self.modifiers:
            if isinstance(item, CrownModifier):
                item.tick()

        # self.tick_effects()

        for bullet_index in range(len(self.bullets)-1, -1, -1):
            bullet = self.bullets[bullet_index]
            if is_outside_box(bullet.position.x, bullet.position.y,
                              config.global_config.box_width,
                              config.global_config.box_height):
                del self.bullets[bullet_index]
                continue

            bullet.move()
            masks = [item for item in self.modifiers if isinstance(item, MaskModifier) and item.player == bullet.player]

            for player in self.players:
                if (bullet.player != player
                        and player.invulnerability_timer.ready()
                        and circles_collide(bullet.position, player.position,
                                            config.global_config.bullet_radius,
                                            config.global_config.player_radius)):

                    player.drop_out(config.global_config.invulnerability_timeout)

                    bullet.player.score += bullet.player.weapon.hit_score

                    for mask in masks:
                        mask.tick()

                    del self.bullets[bullet_index]

                    modifiers_count_before_clean = len(self.modifiers)

                    self.modifiers = [
                        modifier
                        for modifier in self.modifiers
                        if not modifier.detach_from_player(player)
                    ]

                    self.fill_item_spots(modifiers_count_before_clean - len(self.modifiers))

                    break

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

    def tick_effects(self):
        for ind in range(len(self.modifiers) - 1, -1, -1):
            effect = self.modifiers[ind]
            if effect.is_expired():
                del self.modifiers[ind]
            else:
                effect.tick()

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
            ]
        }
