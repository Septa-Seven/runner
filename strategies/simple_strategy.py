import random
import json
import math


class Player:

    def __init__(self, id):
        self.id = id

    def update(self, info):
        self.x = info['position_x']
        self.y = info['position_y']
        self.shot_timeout = info['shot_timeout']
        self.invulnerability_timeout = info['invulnerability_timeout']
        self.bullet_count = info['bullet_count']

    def can_shot(self):
        return self.shot_timeout == 0 and self.bullet_count > 0 and self.invulnerability_timeout == 0


class Strategy:
    def __init__(self):
        config = json.loads(input())
        self.width = config['box_width']
        self.height = config['box_height']

        self.players = {
            player['id']: Player(player['id'])
            for player in config['players']
        }
        self.my_player = self.players[config['my_id']]
        self.target = None
        self.items = None
        self.random_move_ticks = 0
        self.dir_x = 0
        self.dir_y = 0

    def play(self):
        while True:
            state = json.loads(input())

            self.update(state)
            command = self.think()
            print(command)

    def update(self, state):
        self.items = state['items']

        for player_info in state['players']:
            player = self.players[player_info.pop('id')]
            player.update(player_info)

    def think(self):
        return f'{{{self.shot()}{self.move()}}}'

    def move(self):
        item_point = self.get_nearest_item()
        if item_point and self.my_player.invulnerability_timeout == 0:
            item_x, item_y = item_point
            self.dir_x, self.dir_y = direction(self.my_player.x, self.my_player.y, item_x, item_y)
            self.random_move_ticks = 10
        elif self.random_move_ticks == 0:
            self.random_move_ticks = 30
            self.dir_x, self.dir_y = random_direction()
        else:
            self.random_move_ticks -= 1

        return f'"move": {{"direction_x": {self.dir_x}, "direction_y": {self.dir_y}}}'

    def shot(self):
        if self.my_player.can_shot():
            player_point = self.get_random_player()
            if player_point:
                player_x, player_y = player_point
                shot_x, shot_y = smooth_shot(player_x, player_y, self.width, self.height, 60)
                return f'"shot": {{"point_x": {shot_x}, "point_y": {shot_y}}},'

        return ''

    def get_random_player(self):
        player_points = [
            (player.x, player.y)
            for player in self.players.values()
            if self.my_player != player
        ]

        return random.choice(player_points)

    def get_nearest_item(self):
        items_coordinates = [
            (item['spawn_x'], item['spawn_y'])
            if (player := self.players.get(player_id)) is None else
            (player.x, player.y)

            for item in self.items
            if (player_id := item['player_id']) != self.my_player.id
        ]

        return nearest(self.my_player.x, self.my_player.y, items_coordinates)


def smooth_shot(x, y, width, height, smooth):
    x_smooth = x + random.uniform(-1, 1) * smooth
    y_smooth = y + random.uniform(-1, 1) * smooth

    while not on_map(x_smooth, y_smooth, width, height):
        x_smooth = x + random.uniform(-1, 1) * smooth
        y_smooth = y + random.uniform(-1, 1) * smooth

    return x_smooth, y_smooth


def random_direction():
    return random.uniform(-1, 1), random.uniform(-1, 1)


def direction(x1, y1, x2, y2):
    return x2 - x1, y2 - y1


def distance(x1, y1, x2, y2):
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def nearest(x, y, points):
    min_dist = float('inf')
    nearest_ind = None

    for ind, (point_x, point_y) in enumerate(points):
        dist = distance(x, y, point_x, point_y)
        if dist < min_dist:
            min_dist = dist
            nearest_ind = ind

    if nearest_ind is None:
        return None

    return points[nearest_ind]


def on_map(x, y, width, height):
    return 0 <= x <= width and 0 <= y <= height

if __name__ == '__main__':
    Strategy().play()
