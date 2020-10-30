from __future__ import annotations
from game.utils import Vec
from game.timer import Timer
from game.weapons import OneBulletWeapon
from exceptions import ShotError
import config


class Player:
    def __init__(self, id: int, position: Vec):
        self.speed = config.global_config.player_speed

        self.pick_weapon(OneBulletWeapon.pistol())

        self.id = id
        self.position = position
        self.score = 0

        self.invulnerability_timer = Timer()

    def move(self, direction: Vec):
        self.position = self.position + Vec.unit(direction) * self.speed

        # player can't move outside the box
        self.position.x = max(0.0, min(self.position.x, config.global_config.box_width))
        self.position.y = max(0.0, min(self.position.y, config.global_config.box_height))

    def timeouts(self):
        self.invulnerability_timer.tick()
        self.weapon.reload()

    def shot(self, target: Vec, tick: int):
        if not self.invulnerability_timer.ready():
            raise ShotError

        return self.weapon.shot(target, tick)

    def pick_weapon(self, weapon: 'Weapon'):
        self.weapon = weapon
        weapon.attach(self)

    def drop_out(self, invulnerability_timeout):
        self.invulnerability_timer.set(invulnerability_timeout)
        self.pick_weapon(OneBulletWeapon.pistol())
