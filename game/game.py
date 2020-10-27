from __future__ import annotations
from game.player import Player
from game.utils import circles_collide, Vec, is_outside_box
from game.items import item_mapping
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
        self.items = [
            item_mapping[item['id']](Vec(item['spawn_x'], item['spawn_y']))
            for item in config.global_config.items
        ]
        self.modifiers = []

        self.ticks = 0

    def tick(self, commands):
        moves, shots = self.split_actions(commands)

        for move_action in moves:
            move_action.apply()

        for player in self.players:
            player.timeouts()

        # check item collisions
        for item_index in range(len(self.items) - 1, -1, -1):
            item = self.items[item_index]
            player_collides = None
            for player in self.players:
                if (player.invulnerability_timer.ready()
                        and circles_collide(player.position, item.spawn,
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
                del self.items[item_index]
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
            masks = [item for item in self.items if isinstance(item, MaskModifier) and item.player == bullet.player]

            for player in self.players:
                if (bullet.player != player
                        and player.invulnerability_timer.ready()
                        and circles_collide(bullet.position, player.position,
                                            config.global_config.bullet_radius,
                                            config.global_config.player_radius)):

                    player.invulnerability_timer.set(config.global_config.invulnerability_timeout)
                    #
                    # for item in self.items:
                    #     if item.player == player:
                    #         item.detach()

                    bullet.player.score += bullet.player.weapon.hit_score

                    for mask in masks:
                        mask.tick()

                    del self.bullets[bullet_index]

                    break

        self.perform_shots(shots)

        self.ticks += 1

    @staticmethod
    def split_actions(commands):
        moves = []
        shots = []
        for command in commands:
            move, shot = command
            if move is not None:
                moves.append(move)
            if shot is not None:
                shots.append(shot)

        return moves, shots

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
                    'spawn_x': item.spawn.x,
                    'spawn_y': item.spawn.y,
                }
                for item in self.items
            ]
        }
