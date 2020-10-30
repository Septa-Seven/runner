from typing import Callable

from game.modifiers import CrownModifier, MaskModifier, BootsModifier, Modifier, DummyModifier
from game.weapons import ShotgunWeapon, OneBulletWeapon


class Item:
    def pick(self, player) -> Modifier:
        raise NotImplemented


class Crown(Item):
    id = 0

    def pick(self, player):
        crown = CrownModifier()
        crown.attach(player)
        return crown


class Mask(Item):
    id = 1

    def pick(self, player):
        mask = MaskModifier()
        mask.attach(player)
        return mask


class Boots(Item):
    id = 2

    def pick(self, player):
        boots = BootsModifier()
        boots.attach(player)
        return boots


class WeaponItem(Item):
    weapon_constructor: Callable = None

    def pick(self, player):
        player.pick_weapon(self.weapon_constructor())
        m = DummyModifier()
        m.attach(player)
        return m


class ShotgunItem(WeaponItem):
    id = 3
    weapon_constructor = ShotgunWeapon.shotgun


class SniperRifleItem(WeaponItem):
    id = 4
    weapon_constructor = OneBulletWeapon.sniper_rifle


ITEMS = [Crown, Mask, Boots, SniperRifleItem, ShotgunItem]
