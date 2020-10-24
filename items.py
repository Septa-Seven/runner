from utils import Vec
from timer import Timer
import config


class Attachment:
    def __init__(self):
        self.player = None

    def attach(self, player):
        self.player = player

    def detach(self):
        self.player = None


class Modifier(Attachment):
    def attach(self, player):
        super().attach(player)
        self.attach_effect()

    def detach(self):
        self.detach_effect()
        super().detach()

    def attach_effect(self):
        raise NotImplemented

    def detach_effect(self):
        raise NotImplemented


class ItemBase:
    def __init__(self, spawn_position: Vec):
        self.spawn = spawn_position


class Item(ItemBase, Attachment):
    def __init__(self, spawn_position: Vec):
        ItemBase.__init__(self, spawn_position)
        Attachment.__init__(self)


class ModifyingItem(ItemBase, Modifier):
    def __init__(self, spawn_position: Vec):
        ItemBase.__init__(self, spawn_position)
        Modifier.__init__(self)


class Tickable:
    def tick(self):
        self.tick_action()

    def tick_action(self):
        raise NotImplemented


class Temporary(Tickable):
    def __init__(self, ticks: int):
        self.timer = Timer()
        self.timer.set(ticks)

    def tick(self):
        if not self.timer.ready():
            super().tick()

    def is_expired(self):
        return self.timer.ready()


class TemporaryModifier(Modifier, Temporary):
    def __init__(self, ticks):
        Modifier.__init__(self)
        Temporary.__init__(self, ticks)


class Crown(Item, Tickable):
    id = 0

    def tick_action(self):
        if self.player is not None:
            self.player.score += 1


class Mask(ModifyingItem, Tickable):
    id = 1

    def __init__(self, spawn_position):
        super(Mask, self).__init__(spawn_position)
        self.total_hit_score_bonus = 0

    def tick_action(self):
        self.total_hit_score_bonus += config.global_config.mask_hit_score_increment
        self.player.hit_score += config.global_config.mask_hit_score_increment

    def attach_effect(self):
        pass

    def detach_effect(self):
        self.player.hit_score -= self.total_hit_score_bonus
        self.total_hit_score_bonus = 0


class Boots(ModifyingItem):
    id = 2

    def attach_effect(self):
        self.player.speed += config.global_config.boots_speed_effect

    def detach_effect(self):
        self.player.speed -= config.global_config.boots_speed_effect


class Ammunition(ModifyingItem):
    id = 3

    def attach_effect(self):
        self.player.max_bullets += config.global_config.ammunition_max_bullets_effect
        self.player.shot_timeout -= config.global_config.ammunition_shot_timeout_effect
        self.player.reload_timeout -= config.global_config.ammunition_reload_timeout_effect

    def detach_effect(self):
        self.player.max_bullets -= config.global_config.ammunition_max_bullets_effect
        if self.player.bullet_count > self.player.max_bullets:
            self.player.bullet_count = self.player.max_bullets
        self.player.shot_timeout += config.global_config.ammunition_shot_timeout_effect
        self.player.reload_timeout += config.global_config.ammunition_reload_timeout_effect


item_mapping = {
    ind: cls
    for ind, cls in enumerate([Crown, Mask, Ammunition, Boots])
}
