from __future__ import annotations

from typing import Optional
from game.utils import Vec
from game.timer import Timer
from game.weapons import OneBulletWeapon
from game.modifiers import Modifier
from game.items import PistolItem, Item
from exceptions import ShotError
import config


class Movement:
    def __init__(self, position: Vec):
        self.position = position
        self.speed = config.global_config.player_speed
        self.direction = None

    def move(self):
        if self.direction is None:
            return

        self.position = self.position + Vec.unit(self.direction) * self.speed

        # player can't move outside the box
        self.position.x = max(0.0, min(self.position.x, config.global_config.arena_width))
        self.position.y = max(0.0, min(self.position.y, config.global_config.arena_height))

    def set_direction(self, direction: Vec):
        self.direction = direction

    def set_speed(self, speed: float):
        self.speed = speed


class Player:
    def __init__(self, id: int, position: Vec):
        self.id = id
        self.score = 0

        self.movement = Movement(position)

        self.invulnerability = Timer()
        self.dash_cooldown = Timer()
        self.dash = Timer()

        self.items = []
        self.weapon = None
        self.pick_weapon(OneBulletWeapon.pistol())

    def move(self):
        self.movement.move()

    def set_direction(self, direction: Vec):
        if self.dash.is_over():
            self.movement.set_direction(direction)

    def perform_dash(self):
        if (self.invulnerability.is_over()
                and self.dash.is_over()
                and self.dash_cooldown.is_over()):
            self.dash.set(config.global_config.dash_duration)
            self.invulnerability.set(config.global_config.dash_duration)
            self.movement.set_speed(self.movement.speed + config.global_config.dash_speed_bonus)

    def timeouts(self):
        self.invulnerability.tick()
        self.weapon.reload()

        if not self.dash.is_over():
            self.dash.tick()
            if self.dash.is_over():
                self.movement.set_speed(self.movement.speed - config.global_config.dash_speed_bonus)
                self.dash_cooldown.set(config.global_config.dash_cooldown)

        self.dash_cooldown.tick()

    def shot(self, target: Vec, tick: int):
        if not self.invulnerability.is_over():
            raise ShotError

        return self.weapon.shot(target, tick)

    def pick_item(self, item: Item) -> Optional[Modifier]:
        self.items.append(item)
        return item.apply(self)

    def pick_weapon(self, weapon: 'Weapon'):
        self.weapon = weapon
        weapon.attach(self)

    def drop_out(self, invulnerability_cooldown: int):
        self.invulnerability.set(invulnerability_cooldown)
        self.items = []
        self.pick_item(PistolItem())
