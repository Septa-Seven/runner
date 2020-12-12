from game.utils import Vec


class Chainsaw:
    def __init__(self, radius: float, speed: float, path: list[Vec]):
        self.radius = radius
        self.position = path[0]
        self.speed = speed
        self.path = path
        self.target_index = 1
        self.target = self.path[self.target_index]

    def move(self):
        left_to_move = self.speed

        while True:
            current_target_dist = Vec.distance(self.position, self.target)
            if current_target_dist < left_to_move:
                self.position = self.target
                left_to_move -= current_target_dist

                self.target_index += 1
                if self.target_index == len(self.path):
                    self.target_index = 0
                self.target = self.path[self.target_index]
            else:
                if left_to_move != 0:
                    self.position = self.position + Vec.unit(self.target - self.position) * left_to_move

                break
