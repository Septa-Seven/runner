from __future__ import annotations

from typing import List
import math

from game.timer import Timer
from game.modifiers import Attachment
from game.utils import Vec
from exceptions import ShotError

import config


class Bullet:
    def __init__(self, player: 'Player', position: Vec, direction: Vec, speed: float, created_at: int):
        self.player = player
        self.position = position
        self.velocity = direction * speed
        self.created_at = created_at

    def move(self):
        self.position = self.position + self.velocity


class Weapon(Attachment):
    def __init__(self, hit_score: float, max_bullets: int, reload_timeout: int,
                 shot_timeout: int, bullet_speed: float, shot_offset: float):
        super().__init__()

        self.hit_score = hit_score
        self.max_bullets = max_bullets
        self.reload_timeout = reload_timeout
        self.shot_timeout = shot_timeout
        self.shot_offset = shot_offset

        self.bullet_speed = bullet_speed

        self.bullet_count = self.max_bullets

        self.reload_cooldown = Timer()
        self.reload_cooldown.set(self.reload_timeout)

        self.shot_cooldown = Timer()

    def reload(self):
        self.shot_cooldown.tick()

        if self.bullet_count < self.max_bullets:
            self.reload_cooldown.tick()

            if self.reload_cooldown.is_over():
                self.bullet_count += 1
                self.reload_cooldown.set(self.reload_timeout)

    def shot(self, target: Vec, tick: int) -> List[Bullet]:
        if self.bullet_count == 0 or not self.shot_cooldown.is_over():
            raise ShotError

        self.shot_cooldown.set(self.shot_timeout)

        bullets = self.create_bullets(target, tick)
        self.bullet_count -= 1

        return bullets

    def get_shot_direction(self, target: Vec):
        return Vec.unit(target - self.player.movement.position)

    def get_shot_position(self, direction: Vec):
        return self.player.movement.position + direction * self.shot_offset

    def create_bullets(self, target: Vec, tick: int) -> List[Bullet]:
        raise NotImplemented


class OneBulletWeapon(Weapon):
    def create_bullets(self, target: Vec, tick: int) -> List[Bullet]:
        direction = self.get_shot_direction(target)
        shot_position = self.get_shot_position(direction)
        return [Bullet(self.player, shot_position, direction, self.bullet_speed, tick)]

    @classmethod
    def pistol(cls) -> OneBulletWeapon:
        return cls(
            config.global_config.pistol_hit_score,
            config.global_config.pistol_max_bullets,
            config.global_config.pistol_reload_timeout,
            config.global_config.pistol_shot_timeout,
            config.global_config.pistol_bullet_speed,
            config.global_config.pistol_shot_offset
        )

    @classmethod
    def sniper_rifle(cls) -> OneBulletWeapon:
        return cls(
            config.global_config.sniper_rifle_hit_score,
            config.global_config.sniper_rifle_max_bullets,
            config.global_config.sniper_rifle_reload_timeout,
            config.global_config.sniper_rifle_shot_timeout,
            config.global_config.sniper_rifle_bullet_speed,
            config.global_config.sniper_rifle_shot_offset
        )


class ShotgunWeapon(Weapon):
    def create_bullets(self, target: Vec, tick: int) -> List[Bullet]:
        direction = self.get_shot_direction(target)
        shot_position = self.get_shot_position(direction)

        return [
            Bullet(self.player, shot_position, direction, self.bullet_speed, tick),
            Bullet(self.player, shot_position, Vec.rotate(direction, math.pi/24), self.bullet_speed, tick),
            Bullet(self.player, shot_position, Vec.rotate(direction, -math.pi/24), self.bullet_speed, tick)
        ]

    @classmethod
    def shotgun(cls) -> ShotgunWeapon:
        return cls(
            config.global_config.shotgun_hit_score,
            config.global_config.shotgun_max_bullets,
            config.global_config.shotgun_reload_timeout,
            config.global_config.shotgun_shot_timeout,
            config.global_config.shotgun_bullet_speed,
            config.global_config.shotgun_shot_offset
        )
