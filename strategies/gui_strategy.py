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
    KEY_PICK_WEAPON = key.F
    KEY_SHOT = pyglet.window.mouse.LEFT
    KEY_DASH = pyglet.window.mouse.RIGHT

    PLAYER_COLORS = {
        0: (247, 35, 91),
        1: (28, 235, 90),
        2: (32, 227, 217),
        3: (107, 64, 237),
        4: (58, 240, 185),
        5: (200, 237, 66),
        6: (255, 95, 20),
        7: (168, 39, 132)
    }

    ITEM_COLORS = {
        0: (255, 196, 33),
        1: (42, 45, 46),
        2: (181, 132, 53),
        3: (92, 184, 209),
        4: (191, 34, 10),
        5: (133, 232, 35),
    }

    CHAINSAW_COLOR = (120, 120, 120)

    def __init__(self, *args, **kwargs):
        self.game_config = get_message()
        super().__init__(self.game_config['arena']['width'],
                         self.game_config['arena']['height'], *args, **kwargs)

        self.state = None

        self.key_handler = key.KeyStateHandler()
        self.push_handlers(self.key_handler)
        self.shot_point = None
        self.dash_point = None
        self.last_score_diff = {player['id']: 0 for player in self.game_config['players']['initial']}

    def on_mouse_press(self, x, y, button, modifiers):
        if button == self.KEY_SHOT:
            self.shot_point = (x, y)
        elif button == self.KEY_DASH:
            self.dash_point = (x, y)

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

        return {
            'direction_x': x,
            'direction_y': y
        }

    def get_pick_weapon(self):
        return self.key_handler[self.KEY_PICK_WEAPON]

    def get_dash_point(self):
        for player in self.state['players']:
            if player['id'] == self.game_config['my_id']:
                if player['dash_cooldown'] != 0 or player['invulnerability_timeout'] != 0:
                    self.dash_point = None
                    return None

                position_x = player['position_x']
                position_y = player['position_y']

        if self.dash_point is not None:
            data = {
                'direction_x': self.dash_point[0] - position_x,
                'direction_y': self.dash_point[1] - position_y
            }
            self.dash_point = None
            return data

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

        command = {}

        dash = self.get_dash_point()
        if dash:
            command['dash'] = True
            command['move'] = dash
        else:
            command['move'] = self.get_move_direction()

        shot = self.get_shot_point()
        pick_weapon = self.get_pick_weapon()

        if shot:
            command['shot'] = shot
        if pick_weapon:
            command['pick_weapon'] = pick_weapon

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

        player_map = {}
        for player in self.state['players']:
            player_map[player['id']] = player
            color = self.PLAYER_COLORS[player['id']]
            circle = shapes.Circle(player['position_x'], player['position_y'],
                                   self.game_config['players']['radius'], color=color,
                                   group=players_group, batch=batch)
            if player['invulnerability_timeout'] > 0:
                circle.opacity = 100

            figs.append(circle)

            bullets_count = pyglet.shapes.Rectangle(player['position_x'] + 10, player['position_y'] + 10, 10,
                                          player['bullet_count']*2,
                                          color=(100, 100, 100), batch=batch, group=hud_group)
            figs.append(bullets_count)

        players_top = list(player_map.keys())
        players_top.sort(key=lambda player_id: player_map[player_id]['score'], reverse=True)

        for place, player_id in enumerate(players_top):
            player = player_map[player_id]
            color = self.PLAYER_COLORS[player['id']]
            label = pyglet.text.Label(str(player['score']),
                                      font_name='Times New Roman',
                                      font_size=24,
                                      x=self.game_config['arena']['width'] - 32,
                                      y=self.game_config['arena']['height'] - 32 * (2 + place),
                                      anchor_x='right', anchor_y='center', color=color + (255,),
                                      group=hud_group, batch=batch)
            figs.append(label)

        for item in self.state['items']:
            color = self.ITEM_COLORS[item['id']]

            spawn = shapes.Rectangle(item['position_x'] - self.game_config['arena']['item_radius'],
                                     item['position_y'] - self.game_config['arena']['item_radius'],
                                     self.game_config['arena']['item_radius'] * 2,
                                     self.game_config['arena']['item_radius'] * 2,
                                     color=color, group=background_group, batch=batch)
            figs.append(spawn)

        for chainsaw in self.state['chainsaws']:
            circle = shapes.Circle(chainsaw['position_x'], chainsaw['position_y'],
                                   chainsaw['radius'], color=self.CHAINSAW_COLOR,
                                   group=players_group, batch=batch)
            circle.opacity = 190
            figs.append(circle)

        # item_offsets = []
        # for ind in range(len(self.state['items'])):
        #     x = math.cos(math.pi * self.state['ticks']/32 + 2 * math.pi / len(self.state['items']) * ind) * self.game_config['player_radius'] * 2
        #     y = math.sin(math.pi * self.state['ticks']/32 + 2 * math.pi / len(self.state['items']) * ind) * self.game_config['player_radius'] * 2
        #
        #     item_offsets.append((x, y))
        #
        # for player_id, items in player_items.items():
        #     for ind, item in enumerate(items):
        #         x = player_map[player_id]['position_x'] + item_offsets[ind][0]
        #         y = player_map[player_id]['position_y'] + item_offsets[ind][1]
        #         color = self.ITEM_COLORS[item['id']]
        #         circle = shapes.Circle(x, y,
        #                                self.game_config['item_radius'], color=color,
        #                                group=background_group, batch=batch)
        #         figs.append(circle)
        #
        # for item in not_picked:
        #     color = self.ITEM_COLORS[item['id']]
        #     circle = shapes.Circle(item['spawn_x'], item['spawn_y'],
        #                            self.game_config['item_radius'], color=color,
        #                            group=players_group, batch=batch)
        #     figs.append(circle)

        for bullet in self.state['bullets']:
            circle = shapes.Circle(bullet['position_x'], bullet['position_y'], self.game_config['weapons']['bullet_radius'],
                                   color=self.PLAYER_COLORS[bullet['player_id']], group=players_group, batch=batch)
            figs.append(circle)

        tick_label = pyglet.text.Label(str(self.state['ticks']),
                                       font_name='Times New Roman',
                                       font_size=24,
                                       x=self.game_config['arena']['width'] - 32,
                                       y=self.game_config['arena']['height'] - 32,
                                       anchor_x='right', anchor_y='center', color=(20, 20, 50, 255), batch=batch,
                                       group=hud_group)
        figs.append(tick_label)
        batch.draw()


def main():
    config = pyglet.gl.Config(sample_buffers=1, samples=4)
    game_window = GameWindow(config=config, resizable=True)
    pyglet.gl.glClearColor(1, 1, 1, 1)
    pyglet.clock.schedule_interval(game_window.tick, 1/60)
    pyglet.app.run()


if __name__ == '__main__':
    main()
