import random
from utils import is_outside_box, circles_collide, point_in_circle, line_and_circle_collide, Vec


class Player:
    WAVE_COST = 3
    ACTION_TIMEOUT = 10
    BULLET_RELOAD_TIMEOUT = 30
    MAX_BULLET = 3

    def __init__(self, id: int, position: Vec):
        self.id = id
        self.position = position
        self.speed = 4.0
        self.direction = Vec(0.0, 0.0)
        self.radius = 10
        self.score = 0

        self.action_timeout = 0
        self.invulnerability_timeout = 0
        self.bullet_timeout = self.BULLET_RELOAD_TIMEOUT
        self.bullet_count = self.MAX_BULLET

    def change_direction(self, direction: Vec):
        self.direction = direction

    def tick(self, box_width: int, box_height: int):
        self.move(box_width, box_height)
        self.timeouts()

    def move(self, box_width: float, box_height: float):
        self.position = self.position + self.direction * self.speed

        # player can't move outside the box
        self.position.x = max(0.0, min(self.position.x, box_width))
        self.position.y = max(0.0, min(self.position.y, box_height))

    def timeouts(self):
        if self.action_timeout > 0:
            self.action_timeout -= 1

        if self.invulnerability_timeout > 0:
            self.invulnerability_timeout -= 1

        if self.bullet_count < self.MAX_BULLET:
            self.bullet_timeout -= 1

            if self.bullet_timeout == 0:
                self.bullet_count += 1
                self.bullet_timeout = self.BULLET_RELOAD_TIMEOUT

    def shot(self, direction: Vec, tick: int):
        if self.bullet_count > 0 and not direction.is_zero() and self.try_to_set_action_timeout():
            self.bullet_count -= 1
            return Bullet(self, self.position, direction, tick)

    def wave(self, tick: int):
        if self.score >= self.WAVE_COST and self.try_to_set_action_timeout():
            self.score -= self.WAVE_COST
            return Wave(self, self.position, tick)

    def try_to_set_action_timeout(self):
        if self.action_timeout > 0 or self.invulnerability_timeout > 0:
            return False

        self.action_timeout = self.ACTION_TIMEOUT
        return True

    def invulnerability(self):
        if self.invulnerability_timeout == 0:
            self.invulnerability_timeout = 120


class Bullet:
    SPEED = 8.0

    def __init__(self, player: Player, position: Vec, direction: Vec, created_at: int):
        self.player = player
        self.position = position
        self.velocity = Vec.unit(direction) * self.SPEED
        self.created_at = created_at
        self.radius = 5
        self.health = 3

    def move(self, box_width: float, box_height: float):
        self.position = self.position + self.velocity

        # get normal
        if self.position.x < 0:
            x = 1
        elif self.position.x > box_width:
            x = -1
        else:
            x = 0

        if self.position.y < 0:
            y = 1
        elif self.position.y > box_height:
            y = -1
        else:
            y = 0

        # reflect
        if x != 0 or y != 0:
            self.health -= 1
            self.velocity = Vec.reflect(self.velocity, Vec(x, y))

        self.position.x = max(0.0, min(self.position.x, box_width))
        self.position.y = max(0.0, min(self.position.y, box_height))


class Wave:
    SPEED = 10.0

    def __init__(self, player, position: Vec, created_at: int):
        self.position = position
        self.player = player
        self.created_at = created_at
        self.radius = 5.0

    def spread(self):
        self.radius += self.SPEED


class Game:
    def __init__(self, box_width: float, box_height: float):
        self.box_width = box_width
        self.box_height = box_height
        self.players = []
        self.bullets = []
        self.waves = []
        self.ticks = 0

    def tick(self):
        self.bullets[:] = [bullet for bullet in self.bullets if bullet.health <= 0]

        for wave_index in range(len(self.waves), -1, -1):
            wave = self.waves[wave_index]
            if self.box_width < wave.radius:
                self.waves.remove(wave_index)
                continue

            wave.spread()

            self.bullets[:] = [
                bullet
                for bullet in self.bullets
                if (wave.player != bullet.player
                    and bullet.created_at <= wave.created_at
                    and point_in_circle(bullet.position, wave.position, wave.radius))
            ]

        for bullet in self.bullets:
            bullet.move(self.box_width, self.box_height)

        for player in self.players:
            dir = player.construct_direction()
            player.change_direction(dir)

            bullet = player.shot(player.direction, self.ticks)
            if bullet is not None:
                self.bullets.append(bullet)

            wave = player.wave(self.ticks)
            if wave is not None:
                self.waves.append(wave)

            player.tick(self.box_width, self.box_height)

        for bullet_index in range(len(self.bullets)-1, -1, -1):
            bullet = self.bullets[bullet_index]
            for player in self.players:
                if bullet.player != player and player.invulnerability_timeout == 0:
                    if circles_collide(bullet.position, player.position, bullet.radius, player.radius):
                        bullet.player.score += 1
                        player.invulnerability()
                        self.bullets.remove(bullet_index)
                        break

        self.ticks += 1
