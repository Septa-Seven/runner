from typing import Callable, Optional

from game.modifiers import CrownModifier, Modifier
from game.weapons import ShotgunWeapon, OneBulletWeapon


class Item:
    def apply(self, player) -> Optional[Modifier]:
        raise NotImplemented


class Crown(Item):
    id = 0

    def apply(self, player):
        crown = CrownModifier()
        crown.attach(player)
        return crown


class WeaponItem(Item):
    weapon_constructor: Callable = None

    def apply(self, player):
        player.pick_weapon(self.weapon_constructor())


class ShotgunItem(WeaponItem):
    id = 3
    weapon_constructor = ShotgunWeapon.shotgun


class SniperRifleItem(WeaponItem):
    id = 4
    weapon_constructor = OneBulletWeapon.sniper_rifle


class PistolItem(WeaponItem):
    id = 5
    weapon_constructor = OneBulletWeapon.pistol


SPOT_ITEMS = {Crown, SniperRifleItem, ShotgunItem}
