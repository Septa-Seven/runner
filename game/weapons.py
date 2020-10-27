from __future__ import annotations

from typing import List
import math

from game.timer import Timer
from game.modifiers import Attachment
from game.utils import Vec
from exceptions import ShotError

import config


class Bullet:
    def __init__(self, player: 'Player', position: Vec, target: Vec, speed: float, created_at: int):
        self.player = player
        self.position = position
        self.velocity = Vec.unit(target - position) * speed
        self.created_at = created_at

    def move(self):
        self.position = self.position + self.velocity


class Weapon(Attachment):
    def __init__(self, hit_score, max_bullets, reload_timeout, shot_timeout, bullet_speed):
        super().__init__()

        self.hit_score = hit_score
        self.max_bullets = max_bullets
        self.reload_timeout = reload_timeout
        self.shot_timeout = shot_timeout

        self.bullet_speed = bullet_speed

        self.bullet_count = self.max_bullets

        self.reload_timer = Timer()
        self.reload_timer.set(self.reload_timeout)

        self.shot_timer = Timer()

    def reload(self):
        self.shot_timer.tick()

        if self.bullet_count < self.max_bullets:
            self.reload_timer.tick()

            if self.reload_timer.ready():
                self.bullet_count += 1
                self.reload_timer.set(self.reload_timeout)

    def shot(self, target: Vec, tick: int) -> List[Bullet]:
        if self.bullet_count == 0 or not self.shot_timer.ready():
            raise ShotError

        self.shot_timer.set(self.shot_timeout)

        bullets = self.create_bullets(target, tick)
        self.bullet_count -= 1

        return bullets

    def create_bullets(self, target: Vec, tick: int) -> List[Bullet]:
        raise NotImplemented


class OneBulletWeapon(Weapon):
    def create_bullets(self, target: Vec, tick: int) -> List[Bullet]:
        return [Bullet(self.player, self.player.position, target, self.bullet_speed, tick)]

    @classmethod
    def pistol(cls) -> OneBulletWeapon:
        return cls(50, 3, 30, 5, 10)

    @classmethod
    def sniper_rifle(cls) -> OneBulletWeapon:
        return cls(200, 1, 60, 60, 20)


class ShotgunWeapon(Weapon):
    def create_bullets(self, target: Vec, tick: int) -> List[Bullet]:
        direction = target - self.player.position
        return [
            Bullet(self.player, self.player.position, target, self.bullet_speed, tick),
            Bullet(self.player, self.player.position, self.player.position + Vec.rotate(direction, math.pi/12), self.bullet_speed, tick),
            Bullet(self.player, self.player.position, self.player.position + Vec.rotate(direction, -math.pi/12), self.bullet_speed, tick)
        ]

    @classmethod
    def shotgun(cls) -> ShotgunWeapon:
        return cls(50, 3, 120, 30, 6)
