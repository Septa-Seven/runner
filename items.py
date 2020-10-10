import random
from utils import Vec, is_outside_box
import config


class Item:
    def __init__(self, spawn_position: Vec):
        self.spawn = spawn_position
        self.player = None

    def pick(self, player):
        self.player = player

    def drop(self):
        self.player = None


class Tickable:
    def tick(self):
        raise NotImplemented


class Crown(Item, Tickable):
    id = 0

    def tick(self):
        if self.player is not None:
            self.player.score += 1


class Mask(Item):
    id = 1

    def pick(self, player):
        super().pick(player)
        self.player.hit_score += config.global_config.mask_hit_score_effect

    def drop(self):
        self.player.hit_score -= config.global_config.boots_speed_effect
        super().drop()


class Boots(Item):
    id = 2

    def pick(self, player):
        super().pick(player)
        self.player.speed += config.global_config.boots_speed_effect

    def drop(self):
        self.player.speed -= config.global_config.boots_speed_effect
        super().drop()
