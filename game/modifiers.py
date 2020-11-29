class Attachment:
    def __init__(self):
        self.player = None

    def attach(self, player):
        self.player = player

    def detach(self):
        self.player = None

    def try_detach_from_player(self, player) -> bool:
        if self.player is player:
            self.detach()
            return True

        return False


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


class CrownModifier(Attachment, Tickable):
    def tick_action(self):
        if self.player is not None:
            self.player.score += 1
