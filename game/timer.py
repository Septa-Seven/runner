class Timer:
    def __init__(self):
        self.ticks = 0

    def set(self, ticks):
        self.ticks = ticks

    def tick(self):
        if self.ticks > 0:
            self.ticks -= 1

    def ready(self):
        return self.ticks == 0
