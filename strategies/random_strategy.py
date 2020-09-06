import random
import json


directions = [
    (-1, -1), (0, -1), (1, -1),
    (-1, 0), (1, 0),
    (-1, 1), (0, 1), (1, 1),
]


class Unit:
    def __init__(self, id, spawn_x, spawn_y, team):
        self.id = id
        self.team = team
        self.spawn_x = spawn_x
        self.spawn_y = spawn_y
        self.x = spawn_x
        self.y = spawn_y

    def update(self, x, y):
        self.x = x
        self.y = y


def on_map(x, y, map_width, map_height):
    return 0 <= x < map_width and 0 <= y < map_height


def random_move(unit, map_width, map_height):
    while True:
        dir_x, dir_y = random.choice(directions)
        new_x = unit.x + dir_x
        new_y = unit.y + dir_y

        if on_map(new_x, new_y, map_width, map_height):
            break

    return new_x, new_y


def main():
    pass


if __name__ == '__main__':
    main()
