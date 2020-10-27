from game.timer import Timer
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


class CrownModifier(Attachment, Tickable):
    def tick_action(self):
        if self.player is not None:
            self.player.score += 1


class BootsModifier(Modifier):

    def attach_effect(self):
        self.player.speed += config.global_config.boots_speed_effect

    def detach_effect(self):
        self.player.speed -= config.global_config.boots_speed_effect


class MaskModifier(Modifier):

    def __init__(self):
        super().__init__()
        self.total_hit_score_bonus = 0

    def tick_action(self):
        self.total_hit_score_bonus += config.global_config.mask_hit_score_increment
        self.player.hit_score += config.global_config.mask_hit_score_increment

    def attach_effect(self):
        pass

    def detach_effect(self):
        self.player.hit_score -= self.total_hit_score_bonus
        self.total_hit_score_bonus = 0
