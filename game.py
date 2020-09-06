import random

from utils import circles_collide, point_in_circle, Vec
from config import GameConfig


class Player:
    def __init__(self, id: int, position: Vec, config: GameConfig):
        self.config = config

        self.id = id
        self.position = position
        self.score = 0

        # TODO bad variable names
        self.bullet_reload_timeout = self.config.BULLET_RELOAD_TIMEOUT
        self.bullet_count = self.config.MAX_BULLETS
        self.invulnerability_timeout = 0
        self.shot_timeout = 0
        self.blink_timeout = 0

    def move(self, direction: Vec):
        self.position = self.position + direction * self.config.PLAYER_SPEED

        # player can't move outside the box
        self.position.x = max(0.0, min(self.position.x, self.config.BOX_WIDTH))
        self.position.y = max(0.0, min(self.position.y, self.config.BOX_HEIGHT))

    def timeouts(self):
        if self.shot_timeout > 0:
            self.shot_timeout -= 1

        if self.blink_timeout > 0:
            self.blink_timeout -= 1

        if self.invulnerability_timeout > 0:
            self.invulnerability_timeout -= 1

        if self.bullet_count < self.config.MAX_BULLETS:
            self.bullet_reload_timeout -= 1

            if self.bullet_reload_timeout == 0:
                self.bullet_count += 1
                self.bullet_reload_timeout = self.config.BULLET_RELOAD_TIMEOUT

    def shot(self, direction: Vec, tick: int):
        if (self.bullet_count > 0
                and self.shot_timeout == 0
                and self.invulnerability_timeout == 0
                and not direction.is_zero()):
            self.bullet_count -= 1
            self.shot_timeout = self.config.SHOT_TIMEOUT
            return Bullet(self, self.position, direction, tick, self.config)

    def blink(self, direction: Vec):
        if (self.blink_timeout == 0
                and self.invulnerability_timeout == 0
                and not direction.is_zero()):
            self.position = self.position + Vec.unit(direction) * self.config.BLINK_RADIUS
            self.position.x = max(0.0, min(self.position.x, self.config.BOX_WIDTH))
            self.position.y = max(0.0, min(self.position.y, self.config.BOX_HEIGHT))

            self.blink_timeout = self.config.BLINK_TIMEOUT

    def invulnerability(self):
        if self.invulnerability_timeout == 0:
            self.invulnerability_timeout = self.config.INVULNERABILITY_TIMEOUT


class Bullet:
    def __init__(self, player: Player, position: Vec, direction: Vec, created_at: int, config: GameConfig):
        self.config = config
        self.player = player
        self.position = position
        self.velocity = Vec.unit(direction) * self.config.BULLET_SPEED
        self.created_at = created_at
        self.strength = self.config.BULLET_STRENGTH

    def move(self):
        self.position = self.position + self.velocity

        # get normal
        if self.position.x < 0:
            x = 1
        elif self.position.x > self.config.BOX_WIDTH:
            x = -1
        else:
            x = 0

        if self.position.y < 0:
            y = 1
        elif self.position.y > self.config.BOX_HEIGHT:
            y = -1
        else:
            y = 0

        # reflect
        if x != 0 or y != 0:
            self.strength -= 1
            self.velocity = Vec.reflect(self.velocity, Vec(x, y))

        self.position.x = max(0.0, min(self.position.x, self.config.BOX_WIDTH))
        self.position.y = max(0.0, min(self.position.y, self.config.BOX_HEIGHT))


# class Wave:
#     SPEED = 10.0
#
#     def __init__(self, player, position: Vec, created_at: int):
#         self.position = position
#         self.player = player
#         self.created_at = created_at
#         self.radius = 0.0
#
#     def spread(self):
#         self.radius += self.SPEED


class Game:
    def __init__(self, config: GameConfig):
        self.config = config
        self.players = [
            Player(player_id, Vec(random.randint(0, config.BOX_WIDTH), random.randint(0, config.BOX_HEIGHT)), config)
            for player_id in range(config.PLAYERS)
        ]

        self.bullets = []
        self.waves = []
        self.ticks = 0

    def tick(self, players_commands):
        moves = []
        shots = []
        blinks = []
        for client_id, command in players_commands.items():
            move, shot, blink = command
            if move is not None:
                moves.append(move)
            if shot is not None:
                shots.append(shot)
            if blink is not None:
                blinks.append(blink)

        # for wave_index in range(len(self.waves), -1, -1):
        #     wave = self.waves[wave_index]
        #     if self.config.BOX_WIDTH < wave.radius:
        #         self.waves.remove(wave_index)
        #         continue
        #
        #     wave.spread()
        #
        #     self.bullets[:] = [
        #         bullet
        #         for bullet in self.bullets
        #         if (wave.player != bullet.player
        #             and bullet.created_at <= wave.created_at
        #             and point_in_circle(bullet.position, wave.position, wave.radius))
        #     ]

        for bullet in self.bullets:
            bullet.move()

        self.bullets[:] = [bullet for bullet in self.bullets if bullet.strength > 0]

        for blink in blinks:
            blink.player.blink(blink.direction)

        for move in moves:
            move.player.move(move.direction)

        for player in self.players:
            player.timeouts()

        for shot in shots:
            bullet = shot.player.shot(shot.direction, self.ticks)
            if bullet is not None:
                self.bullets.append(bullet)

        # for player in self.players:
        #     wave = player.wave(self.ticks)
        #     if wave is not None:
        #         self.waves.append(wave)
        #
        #     player.tick(self.box_width, self.box_height)

        for bullet_index in range(len(self.bullets)-1, -1, -1):
            bullet = self.bullets[bullet_index]
            for player in self.players:
                if bullet.player != player and player.invulnerability_timeout == 0:
                    if circles_collide(bullet.position, player.position,
                                       self.config.BULLET_RADIUS, self.config.PLAYER_RADIUS):
                        bullet.player.score += 1
                        player.invulnerability()
                        self.bullets.pop(bullet_index)
                        break

        self.ticks += 1

    def is_ended(self):
        return self.ticks == self.config.MAX_TICKS

    def get_player_by_id(self, player_id):
        for player in self.players:
            if player.id == player_id:
                return player

    def get_state(self):
        return {
            'ticks': self.ticks,
            'players': [
                {
                    'id': player.id, 'position_x': player.position.x, 'position_y': player.position.y,
                    'bullet_count': player.bullet_count, 'bullet_reload_timeout': player.bullet_reload_timeout,
                    'invulnerability_timeout': player.invulnerability_timeout,
                    'blink_timeout': player.blink_timeout,
                    'shot_timeout': player.shot_timeout, 'score': player.score
                }
                for player in self.players
            ],
            'bullets': [
                {
                    'player_id': bullet.player.id, 'position_x': bullet.position.x, 'position_y': bullet.position.y,
                    'velocity_x': bullet.velocity.x, 'velocity_y': bullet.velocity.y, 'strength': bullet.strength
                }
                for bullet in self.bullets
            ]
        }
