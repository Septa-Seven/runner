import random
import pyglet
from pyglet import shapes
from pyglet.window import key
from utils import is_outside_box, circles_collide, point_in_circle, line_and_circle_collide, Vec


class Player:
    WAVE_COST = 3
    ACTION_TIMEOUT = 10
    BULLET_RELOAD_TIMEOUT = 30
    MAX_BULLET = 3

    def __init__(self, id: int, position: Vec):
        self.id = id
        self.position = position
        self.speed = 4.0
        self.direction = Vec(0.0, 0.0)
        self.radius = 10
        self.action_timeout = 0
        self.invulnerability_timeout = 0
        self.bullet_timeout = self.BULLET_RELOAD_TIMEOUT
        self.bullet_count = self.MAX_BULLET

        self.score = 0

    def change_direction(self, direction: Vec):
        self.direction = direction

    def tick(self, box_width, box_height):
        self.move(box_width, box_height)
        self.timeouts()

    def timeouts(self):
        if self.action_timeout > 0:
            self.action_timeout -= 1

        if self.invulnerability_timeout > 0:
            self.invulnerability_timeout -= 1

        if self.bullet_count < self.MAX_BULLET:
            self.bullet_timeout -= 1

            if self.bullet_timeout == 0:
                self.bullet_count += 1
                self.bullet_timeout = self.BULLET_RELOAD_TIMEOUT

    def move(self, box_width: float, box_height: float):
        self.position = self.position + self.direction * self.speed

        # player can't move outside the box
        self.position.x = max(0.0, min(self.position.x, box_width))
        self.position.y = max(0.0, min(self.position.y, box_height))

    def shot(self, direction: Vec, tick: int):
        if self.bullet_count > 0 and not direction.is_zero() and self.try_to_set_action_timeout():
            self.bullet_count -= 1
            return Bullet(self, self.position, direction, tick)

    def wave(self, tick: int):
        if self.score >= self.WAVE_COST and self.try_to_set_action_timeout():
            self.score -= self.WAVE_COST
            return Wave(self, self.position, tick)
    #
    # def line_bullet(self, direction: Vec, tick: int):
    #     if not direction.is_zero() and self.try_to_set_action_timeout():
    #         return LineBullet(self, self.position, direction, tick)

    def try_to_set_action_timeout(self):
        if self.action_timeout > 0 or self.invulnerability_timeout > 0:
            return False

        self.action_timeout = self.ACTION_TIMEOUT
        return True

    def invulnerability(self):
        if self.invulnerability_timeout == 0:
            self.invulnerability_timeout = 120


class KeyboardPlayer1(Player):
    KEY_LEFT = key.A
    KEY_RIGHT = key.D
    KEY_UP = key.W
    KEY_DOWN = key.S
    KEY_BULLET = key.C
    KEY_LINE_BULLET = key.V
    KEY_WAVE = key.B

    def __init__(self, key_handler, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.key_handler = key_handler

    def construct_direction(self):
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

        return Vec(x, y)

    def shot(self, dir, tick):
        if self.key_handler[self.KEY_BULLET]:
            return super().shot(dir, tick)

    # def line_bullet(self, direction, tick):
    #     if self.key_handler[self.KEY_LINE_BULLET]:
    #         return super().line_bullet(direction, tick)

    def wave(self, tick):
        if self.key_handler[self.KEY_WAVE]:
            return super().wave(tick)


class KeyboardPlayer2(KeyboardPlayer1):
    KEY_LEFT = key.LEFT
    KEY_RIGHT = key.RIGHT
    KEY_UP = key.UP
    KEY_DOWN = key.DOWN
    KEY_BULLET = key.I
    KEY_LINE_BULLET = key.O
    KEY_WAVE = key.P


class MousePlayer(KeyboardPlayer1):
    def __init__(self, window, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.shot_dir = None
        self.line_dir = None

        @window.event
        def on_mouse_press(x, y, button, modifier):
            if button == pyglet.window.mouse.LEFT:
                self.shot_dir = Vec(x, y) - self.position
            if button == pyglet.window.mouse.RIGHT:
                self.line_dir = Vec(x, y) - self.position

    def shot(self, dir, tick):
        if self.shot_dir is not None:
            bullet = Player.shot(self, self.shot_dir, tick)
            self.shot_dir = None
            return bullet

    # def line_bullet(self, dir, tick):
    #     if self.line_dir is not None:
    #         bullet = Player.line_bullet(self, self.line_dir, tick)
    #         self.line_dir = None
    #         return bullet


class Bullet:
    def __init__(self, player: Player, position: Vec, direction: Vec, created_at: int):
        self.player = player
        self.position = position
        speed = 8.0
        self.velocity = Vec.unit(direction) * speed
        self.created_at = created_at
        self.radius = 5
        self.health = 3

    def move(self, box_width: float, box_height: float):
        self.position = self.position + self.velocity

        # get normal
        if self.position.x < 0:
            x = 1
        elif self.position.x > box_width:
            x = -1
        else:
            x = 0

        if self.position.y < 0:
            y = 1
        elif self.position.y > box_height:
            y = -1
        else:
            y = 0

        # reflect
        if x != 0 or y != 0:
            self.health -= 1
            self.velocity = Vec.reflect(self.velocity, Vec(x, y))

        self.position.x = max(0.0, min(self.position.x, box_width))
        self.position.y = max(0.0, min(self.position.y, box_height))


class LineBullet:
    def __init__(self, player: Player, position: Vec, direction: Vec, created_at: int):
        self.player = player
        self.start = position
        self.position = position
        speed = 2.5
        self.velocity = Vec.unit(direction) * speed
        self.created_at = created_at

    def move(self):
        self.position = self.position + self.velocity


class Wave:
    def __init__(self, player, position: Vec, created_at: int):
        self.position = position
        self.player = player
        self.created_at = created_at
        self.radius = 5.0
        self.speed = 10.0

    def spread(self):
        self.radius += self.speed


class Game:
    def __init__(self, window, key_handler, box_width: float, box_height: float):
        self.box_width = box_width
        self.box_height = box_height
        # self.players = [Player(0, Vec(16.0, 16.0)), Player(1, Vec(box_width - 16.0, box_height - 16.0)),
        #                 Player(2, Vec(16.0, box_height - 16.0)), Player(3, Vec(box_width - 16.0, 16.0)),
        self.players = [KeyboardPlayer2(key_handler, 2, Vec(box_width/2, box_height/2)),
                        MousePlayer(window, key_handler, 4, Vec(box_width/3, box_height/3))]
        self.bullets = set()
        self.waves = set()
        self.ticks = 0

    def tick(self):
        remove_waves = set()
        for wave in self.waves:
            wave.spread()

            if self.box_width < wave.radius:
                remove_waves.add(wave)

        self.waves -= remove_waves

        for wave in self.waves:
            remove_bullets = set()

            for bullet in self.bullets:
                if (wave.player != bullet.player
                        and bullet.created_at <= wave.created_at
                        and point_in_circle(bullet.position, wave.position, wave.radius)):
                    remove_bullets.add(bullet)

            self.bullets -= remove_bullets

        remove_bullets = set()
        for bullet in self.bullets:
            if bullet.health <= 0:
                remove_bullets.add(bullet)
        self.bullets -= remove_bullets

        for bullet in self.bullets:
            bullet.move(self.box_width, self.box_height)

        for player in self.players:
            if isinstance(player, KeyboardPlayer1) or isinstance(player, KeyboardPlayer2):
                dir = player.construct_direction()
                player.change_direction(dir)

                bullet = player.shot(player.direction, self.ticks)
                if bullet is not None:
                    self.bullets.add(bullet)

                wave = player.wave(self.ticks)
                if wave is not None:
                    self.waves.add(wave)

                player.tick(self.box_width, self.box_height)
                continue

            player.tick(self.box_width, self.box_height)

            if self.ticks % 60 != 0:
                continue

            dir = Vec(random.randint(-1, 1), random.randint(-1, 1))
            player.change_direction(dir)

            if random.randint(1, 10) == 1:
                dir = Vec(random.randint(-1, 1) * random.random(), random.randint(-1, 1) * random.random())
                if dir.x != 0 or dir.y != 0:
                    bullet = player.shot(dir, self.ticks)
                    if bullet is not None:
                        self.bullets.add(bullet)

            # if random.randint(1, 15) == 1:
            #     wave = player.wave(self.ticks)
            #     self.waves.add(wave)

            # if random.randint(1, 5) == 1:
            #     dir = Vec(random.randint(-1, 1) * random.random(), random.randint(-1, 1) * random.random())
            #     if dir.x != 0 or dir.y != 0:
            #         line_bullet = player.line_bullet(dir, self.ticks)
            #         if line_bullet is not None:
            #             self.line_bullets.add(line_bullet)

        remove_bullets = set()
        for bullet in self.bullets:
            for player in self.players:
                if bullet.player != player and player.invulnerability_timeout == 0:
                    if circles_collide(bullet.position, player.position, bullet.radius, player.radius):
                        player.invulnerability()
                        # self.players.remove(player)
                        remove_bullets.add(bullet)
                        bullet.player.score += 1
                        break

        for bullet in remove_bullets:
            self.bullets.remove(bullet)

        self.ticks += 1


class GameWindow(pyglet.window.Window):
    def __init__(self, width, height):
        super().__init__(width, height)
        key_handler = key.KeyStateHandler()
        self.push_handlers(key_handler)
        self.game = Game(self, key_handler, width, height)

    def tick(self, dt):
        self.game.tick()

    def on_draw(self):
        self.clear()
        for player in self.game.players:
            color = 20 + 25 * player.id
            color = (int(color/2), int((color**2 - 50)/4), color)
            circle = shapes.Circle(player.position.x, player.position.y, player.radius,
                                   color=color)
            if player.invulnerability_timeout > 0:
                circle.opacity = 60

            label = pyglet.text.Label(str(player.score),
                                      font_name='Times New Roman',
                                      font_size=24,
                                      x=self.game.box_width - 32, y=self.game.box_height - 32 * (1 + player.id),
                                      anchor_x='right', anchor_y='center', color=color + (255,))

            arc = pyglet.shapes.Rectangle(player.position.x + 16, player.position.y + 16, 10,
                                          player.bullet_count/player.MAX_BULLET*10, color=(100, 100, 100))

            arc.draw()
            circle.draw()
            label.draw()

        for bullet in self.game.bullets:
            color = 20 + 25 * bullet.player.id
            circle = shapes.Circle(bullet.position.x, bullet.position.y, bullet.radius,
                                   color=(int(color/2), int((color**2 - 50)/4), color))
            circle.draw()

        for wave in self.game.waves:
            color = 20 + 25 * wave.player.id
            circle = shapes.Circle(wave.position.x, wave.position.y, wave.radius,
                                   color=(int(color/2), int((color**2 - 50) / 4), color))
            circle.opacity = 100
            circle.draw()

        tick_label = pyglet.text.Label(str(self.game.ticks),
                                      font_name='Times New Roman',
                                      font_size=24,
                                      x=self.game.box_width - 32, y=self.game.box_height - 32,
                                      anchor_x='right', anchor_y='center', color=(20, 20, 50, 255))
        tick_label.draw()


game_window = GameWindow(1024, 700)
pyglet.gl.glClearColor(1,1,1,1)
pyglet.clock.schedule_interval(game_window.tick, 0.01)
pyglet.app.run()