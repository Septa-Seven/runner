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

    PLAYER_COLORS = {
        0: (10, 200, 32),
        1: (10, 200, 200),
        2: (234, 23, 12),
        3: (123, 245, 32)
    }

    def __init__(self):
        self.game_config = get_message()
        super().__init__(self.game_config['BOX_WIDTH'], self.game_config['BOX_HEIGHT'])

        self.state = None

        self.key_handler = key.KeyStateHandler()
        self.push_handlers(self.key_handler)
        self.shot_direction = None

    def on_mouse_press(self, x, y, button, modifiers):
        if button == self.KEY_SHOT:
            self.shot_direction = (x, y)

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

    def get_shot_direction(self, x, y):
        if self.shot_direction is not None:
            data = {
                'direction_x': self.shot_direction[0] - x,
                'direction_y': self.shot_direction[1] - y
            }
            self.shot_direction = None
            return data

    def tick(self, dt):
        self.state = get_message()

        for player in self.state['players']:
            if player['id'] == self.game_config['my_id']:
                x = player['position_x']
                y = player['position_y']
                break
        else:
            return

        move = self.get_move_direction()
        shot = self.get_shot_direction(x, y)

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
        for player in self.state['players']:
            color = self.PLAYER_COLORS[player['id']]
            circle = shapes.Circle(player['position_x'], player['position_y'],
                                   self.game_config['PLAYER_RADIUS'], color=color)

            if player['invulnerability_timeout'] > 0:
                circle.opacity = 60

            label = pyglet.text.Label(str(player['score']),
                                      font_name='Times New Roman',
                                      font_size=24,
                                      x=self.game_config['BOX_WIDTH'] - 32,
                                      y=self.game_config['BOX_HEIGHT'] - 32 * (2 + player['id']),
                                      anchor_x='right', anchor_y='center', color=color + (255,))

            arc = pyglet.shapes.Rectangle(player['position_x'] + 16, player['position_y'] + 16, 10,
                                          player['bullet_count']/self.game_config['MAX_BULLETS']*10,
                                          color=(100, 100, 100))

            arc.draw()
            circle.draw()
            label.draw()

        for bullet in self.state['bullets']:
            circle = shapes.Circle(bullet['position_x'], bullet['position_y'], self.game_config['BULLET_RADIUS'],
                                   color=self.PLAYER_COLORS[bullet['player_id']])
            circle.draw()

        # for wave in self.game.waves:
        #     color = 20 + 25 * wave.player.id
        #     circle = shapes.Circle(wave.position.x, wave.position.y, wave.radius,
        #                            color=(int(color/2), int((color**2 - 50) / 4), color))
        #     circle.opacity = 100
        #     circle.draw()

        tick_label = pyglet.text.Label(str(self.state['ticks']),
                                       font_name='Times New Roman',
                                       font_size=24,
                                       x=self.game_config['BOX_WIDTH'] - 32, y=self.game_config['BOX_HEIGHT'] - 32,
                                       anchor_x='right', anchor_y='center', color=(20, 20, 50, 255))
        tick_label.draw()


def main():
    game_window = GameWindow()
    pyglet.gl.glClearColor(1,1,1,1)
    pyglet.clock.schedule_interval(game_window.tick, 1/60)
    pyglet.app.run()


if __name__ == '__main__':
    main()
