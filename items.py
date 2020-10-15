from utils import Vec
import config


class Item:
    def __init__(self, spawn_position: Vec):
        self.spawn = spawn_position
        self.player = None

    def pick(self, player):
        self.player = player

    def drop(self):
        self.player = None

    @classmethod
    def mapping(cls):
        return {item_cls.id: item_cls for item_cls in cls.__subclasses__()}


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


class Pocket(Item):
    id = 3

    def pick(self, player):
        super().pick(player)
        self.player.max_bullets += config.global_config.pocket_max_bullets_effect

    def drop(self):
        self.player.max_bullets -= config.global_config.pocket_max_bullets_effect
        if self.player.bullet_count > self.player.max_bullets:
            self.player.bullet_count = self.player.max_bullets

        super().drop()


class Dragon(Item):
    id = 4

    def pick(self, player):
        super().pick(player)
        self.player.shot_timeout -= config.global_config.dragon_shot_timeout_effect

    def drop(self):
        self.player.shot_timeout += config.global_config.dragon_shot_timeout_effect
        super().drop()


class Leaf(Item):
    id = 5

    def pick(self, player):
        super().pick(player)
        self.player.reload_timeout -= config.global_config.leaf_reload_timeout_effect

    def drop(self):
        self.player.reload_timeout += config.global_config.leaf_reload_timeout_effect
        super().drop()
