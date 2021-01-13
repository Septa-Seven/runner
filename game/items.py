from typing import Optional

from game.modifiers import CrownModifier, Modifier
from game.weapons import Shotgun, Pistol, SniperRifle

import config


class Item:
    def apply(self, player) -> Optional[Modifier]:
        raise NotImplemented


class CrownItem(Item):
    id = 0

    def apply(self, player):
        crown = CrownModifier()
        crown.attach(player)
        return crown


class WeaponItem(Item):

    def apply(self, player):
        player.pick_weapon(self.construct_weapon())

    def construct_weapon(self):
        raise NotImplementedError


class ShotgunItem(WeaponItem):
    id = 1

    def construct_weapon(self):
        return Shotgun(
            config.global_config.items.weapons.shotgun.hit_score,
            config.global_config.items.weapons.shotgun.initial_bullets,
            config.global_config.items.weapons.shotgun.shot_timeout,
            config.global_config.items.weapons.shotgun.bullet_speed,
            config.global_config.items.weapons.shotgun.shot_offset
        )


class SniperRifleItem(WeaponItem):
    id = 2

    def construct_weapon(self):
        return SniperRifle(
            config.global_config.items.weapons.sniper_rifle.hit_score,
            config.global_config.items.weapons.sniper_rifle.initial_bullets,
            config.global_config.items.weapons.sniper_rifle.shot_timeout,
            config.global_config.items.weapons.sniper_rifle.bullet_speed,
            config.global_config.items.weapons.sniper_rifle.shot_offset
        )


class PistolItem(WeaponItem):
    id = 3

    def construct_weapon(self):
        return Pistol(
            config.global_config.items.weapons.pistol.hit_score,
            config.global_config.items.weapons.pistol.initial_bullets,
            config.global_config.items.weapons.pistol.shot_timeout,
            config.global_config.items.weapons.pistol.bullet_speed,
            config.global_config.items.weapons.pistol.shot_offset
        )


WEAPON_ITEM_CLASSES = [SniperRifleItem, ShotgunItem]
