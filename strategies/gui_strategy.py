import json

import pyglet
from pyglet import shapes
from pyglet.window import key


def get_message():
    return json.loads(input())


class GameWindow(pyglet.window.Window):
    KEY_LEFT = key.A
    KEY_RIGHT = key.D
    KEY_UP = key.W
    KEY_DOWN = key.S
    KEY_SHOT = pyglet.window.mouse.LEFT
    KEY_BLINK = pyglet.window.mouse.RIGHT

    PLAYER_COLORS = {
        0: (247, 35, 91),
        1: (28, 235, 90),
        2: (32, 227, 217),
        3: (107, 64, 237)
    }

    def __init__(self):
        self.game_config = get_message()
        super().__init__(self.game_config['box_width'], self.game_config['box_height'])

        self.state = None

        self.key_handler = key.KeyStateHandler()
        self.push_handlers(self.key_handler)
        self.shot_point = None
        self.blink_direction = None

    def on_mouse_press(self, x, y, button, modifiers):
        if button == self.KEY_SHOT:
            self.shot_point = (x, y)
        if button == self.KEY_BLINK:
            self.blink_direction = (x, y)

    def get_move_direction(self):
        x = 0
        y = 0
        if self.key_handler[self.KEY_LEFT]:
            x -= 1
        if self.key_handler[self.KEY_RIGHT]:
            x += 1
        if self.key_handler[self.KEY_UP]:
            y += 1
        if self.key_handler[self.KEY_DOWN]:
            y -= 1

        if x != 0 or y != 0:
            return {
                'direction_x': x,
                'direction_y': y
            }

    def get_shot_point(self):
        if self.shot_point is not None:
            data = {
                'point_x': self.shot_point[0],
                'point_y': self.shot_point[1]
            }
            self.shot_point = None
            return data

    def tick(self, dt):
        self.state = get_message()

        move = self.get_move_direction()
        shot = self.get_shot_point()

        command = {}
        if move:
            command['move'] = move
        if shot:
            command['shot'] = shot

        print(json.dumps(command), flush=True)

    def on_draw(self):
        if self.state is None:
            return

        self.clear()

        batch = pyglet.graphics.Batch()
        background_group = pyglet.graphics.OrderedGroup(0)
        players_group = pyglet.graphics.OrderedGroup(1)
        hud_group = pyglet.graphics.OrderedGroup(2)
        figs = []

        for spawn in self.game_config['spawns']:
            color = self.PLAYER_COLORS[spawn['player_id']]
            circle = shapes.Circle(spawn['spawn_x'], spawn['spawn_y'],
                                   self.game_config['player_radius'], color=color,
                                   group=background_group, batch=batch)
            circle.opacity = 60

            figs.append(circle)

        for player in self.state['players']:
            color = self.PLAYER_COLORS[player['id']]
            circle = shapes.Circle(player['position_x'], player['position_y'],
                                   self.game_config['player_radius'], color=color,
                                   group=players_group, batch=batch)
            if player['invulnerability_timeout'] > 0:
                circle.opacity = 100

            figs.append(circle)

            label = pyglet.text.Label(str(player['score']),
                                      font_name='Times New Roman',
                                      font_size=24,
                                      x=self.game_config['box_width'] - 32,
                                      y=self.game_config['box_height'] - 32 * (2 + player['id']),
                                      anchor_x='right', anchor_y='center', color=color + (255,),
                                      group=hud_group, batch=batch)
            figs.append(label)
            bullets_count = pyglet.shapes.Rectangle(player['position_x'] + 10, player['position_y'] + 10, 10,
                                          player['bullet_count']/self.game_config['max_bullets']*10,
                                          color=(100, 100, 100), batch=batch, group=hud_group)
            figs.append(bullets_count)

        for bullet in self.state['bullets']:
            circle = shapes.Circle(bullet['position_x'], bullet['position_y'], self.game_config['bullet_radius'],
                                   color=self.PLAYER_COLORS[bullet['player_id']], group=players_group, batch=batch)
            figs.append(circle)

        circle = shapes.Circle(self.state['crown']['position_x'], self.state['crown']['position_y'],
                               self.game_config['crown_radius'], color=(255, 197, 23),
                               group=players_group, batch=batch)
        figs.append(circle)

        tick_label = pyglet.text.Label(str(self.state['ticks']),
                                       font_name='Times New Roman',
                                       font_size=24,
                                       x=self.game_config['box_width'] - 32, y=self.game_config['box_height'] - 32,
                                       anchor_x='right', anchor_y='center', color=(20, 20, 50, 255), batch=batch,
                                       group=hud_group)
        figs.append(tick_label)
        batch.draw()


def main():
    game_window = GameWindow()
    pyglet.gl.glClearColor(1, 1, 1, 1)
    pyglet.clock.schedule_interval(game_window.tick, 1/60)
    pyglet.app.run()


if __name__ == '__main__':
    main()
