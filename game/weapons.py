from __future__ import annotations

import math
from typing import Optional

from game.timer import Timer
from game.modifiers import Attachment
from game.utils import Vec

import config


class ShotError(Exception):
    pass


class NoAmmoError(Exception):
    pass


# TODO purpose of created_at is unclear
class Bullet:
    def __init__(self, player: 'Player', position: Vec, direction: Vec, speed: float, created_at: int):
        self.player = player
        self.position = position
        self.velocity = direction * speed
        self.created_at = created_at

    def move(self):
        self.position = self.position + self.velocity


class Weapon(Attachment):
    def __init__(self, hit_score: float, bullet_count: Optional[int], shot_timeout: int,
                 bullet_speed: float, shot_offset: float):
        super().__init__()

        self.hit_score = hit_score
        self.shot_timeout = shot_timeout
        self.shot_offset = shot_offset

        self.bullet_speed = bullet_speed
        self.bullet_count = bullet_count

        self.shot_cooldown = Timer()

    def tick(self):
        self.shot_cooldown.tick()

    def shot(self, target: Vec, tick: int) -> tuple[list[Bullet], bool]:
        if not self.shot_cooldown.is_over():
            raise ShotError

        self.shot_cooldown.set(self.shot_timeout)

        if self.bullet_count == -1:
            is_last_shot = False
        else:
            is_last_shot = self.bullet_count == 1
            self.bullet_count -= 1

        return self.create_bullets(target, tick), is_last_shot

    def get_shot_direction(self, target: Vec) -> Vec:
        return Vec.unit(target - self.player.movement.position)

    def get_shot_position(self, direction: Vec) -> Vec:
        return self.player.movement.position + direction * self.shot_offset

    def create_bullets(self, target: Vec, tick: int) -> list[Bullet]:
        raise NotImplementedError


class OneBulletWeapon(Weapon):
    def create_bullets(self, target: Vec, tick: int) -> list[Bullet]:
        direction = self.get_shot_direction(target)
        shot_position = self.get_shot_position(direction)
        return [Bullet(self.player, shot_position, direction, self.bullet_speed, tick)]

    @classmethod
    def pistol(cls) -> OneBulletWeapon:
        return cls(
            config.global_config.weapons.pistol.hit_score,
            config.global_config.weapons.pistol.initial_bullets,
            config.global_config.weapons.pistol.shot_timeout,
            config.global_config.weapons.pistol.bullet_speed,
            config.global_config.weapons.pistol.shot_offset
        )

    @classmethod
    def sniper_rifle(cls) -> OneBulletWeapon:
        return cls(
            config.global_config.weapons.sniper_rifle.hit_score,
            config.global_config.weapons.sniper_rifle.initial_bullets,
            config.global_config.weapons.sniper_rifle.shot_timeout,
            config.global_config.weapons.sniper_rifle.bullet_speed,
            config.global_config.weapons.sniper_rifle.shot_offset
        )


class ShotgunWeapon(Weapon):
    def create_bullets(self, target: Vec, tick: int) -> list[Bullet]:
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
            config.global_config.weapons.shotgun.hit_score,
            config.global_config.weapons.shotgun.initial_bullets,
            config.global_config.weapons.shotgun.shot_timeout,
            config.global_config.weapons.shotgun.bullet_speed,
            config.global_config.weapons.shotgun.shot_offset
        )
