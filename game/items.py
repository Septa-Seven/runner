from typing import Optional

from game.utils import Vec
from game.modifiers import CrownModifier, MaskModifier, BootsModifier, Modifier
from game.weapons import ShotgunWeapon, OneBulletWeapon


class Item:
    def __init__(self, spawn_position: Vec):
        self.spawn = spawn_position

    def pick(self, player) -> Optional[Modifier]:
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


class ShotgunItem(Item):
    id = 3

    def pick(self, player):
        player.pick_weapon(ShotgunWeapon.shotgun())


class PistolItem(Item):
    id = 4

    def pick(self, player):
        player.pick_weapon(OneBulletWeapon.pistol())


class SniperRifleItem(Item):
    id = 5

    def pick(self, player):
        player.pick_weapon(OneBulletWeapon.sniper_rifle())


item_mapping = {
    cls.id: cls
    for cls in [Crown, Mask, Boots, SniperRifleItem, PistolItem, ShotgunItem]
}
