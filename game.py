from utils import circles_collide, point_in_circle, Vec, is_outside_box
from config import GameConfig
import random


class Map:
    def __init__(self, width, height):
        self.tiles = [[1.0]*width for _ in range(height)]

    def decrease(self, x: int, y: int, value: float):
        self.tiles[y][x] = max(0.0, self.tiles[y][x] - value)

    def is_void(self, x: int, y: int):
        return self.tiles[y][x] == 0.0

    def top_tiles(self):
        top_tiles = []
        max_strength = 0.0
        for y, row in enumerate(self.tiles):
            for x, tile_strength in enumerate(row):
                if max_strength < tile_strength:
                    max_strength = tile_strength
                    top_tiles = [(x, y)]
                elif tile_strength == max_strength:
                    top_tiles.append((x, y))
        return top_tiles

    def unbroken_tiles(self):
        return [(x, y)
                for y, row in enumerate(self.tiles)
                for x, tile_strength in enumerate(row)
                if tile_strength != 0.0]


class Player:
    def __init__(self, id: int, position: Vec, config: GameConfig):
        self.config = config

        self.id = id
        self.position = position
        self.score = 0

        self.bullet_reload_timeout = self.config.BULLET_RELOAD_TIMEOUT
        self.bullet_count = self.config.MAX_BULLETS
        self.invulnerability_timeout = 0
        self.shot_timeout = 0
        self.dash_timeout = 0

    def move(self, direction: Vec):
        self.position = self.position + direction * self.config.PLAYER_SPEED

        # player can't move outside the box
        self.position.x = max(0.0, min(self.position.x, self.config.BOX_WIDTH - 1))
        self.position.y = max(0.0, min(self.position.y, self.config.BOX_HEIGHT - 1))

    def timeouts(self):
        if self.shot_timeout > 0:
            self.shot_timeout -= 1

        if self.dash_timeout > 0:
            self.dash_timeout -= 1

        if self.invulnerability_timeout > 0:
            self.invulnerability_timeout -= 1

        if self.bullet_count < self.config.MAX_BULLETS:
            self.bullet_reload_timeout -= 1

            if self.bullet_reload_timeout == 0:
                self.bullet_count += 1
                self.bullet_reload_timeout = self.config.BULLET_RELOAD_TIMEOUT

    def shot(self, target: Vec, tick: int):
        if (self.bullet_count > 0
                and self.shot_timeout == 0
                and self.invulnerability_timeout == 0):
            self.bullet_count -= 1
            self.shot_timeout = self.config.SHOT_TIMEOUT
            return Bullet(self, self.position, target, tick, self.config)

    # def dash(self, dash_position: Vec):
    #     if self.dash_timeout == 0 and self.invulnerability_timeout == 0:
    #         dash_position.x = max(0.0, min(dash_position.x, self.config.BOX_WIDTH))
    #         dash_position.y = max(0.0, min(dash_position.y, self.config.BOX_HEIGHT))
    #
    #         self.position = self.position + Vec.unit(dash_position) * self.config.BLINK_RADIUS
    #         self.position.x = max(0.0, min(self.position.x, self.config.BOX_WIDTH))
    #         self.position.y = max(0.0, min(self.position.y, self.config.BOX_HEIGHT))
    #
    #         self.dash_timeout = self.config.DASH_TIMEOUT

    # def invulnerability(self):
    #     if self.invulnerability_timeout == 0:
    #         self.invulnerability_timeout = self.config.INVULNERABILITY_TIMEOUT


class Bullet:
    def __init__(self, player: Player, position: Vec, target: Vec, created_at: int, config: GameConfig):
        self.config = config
        self.player = player
        self.position = position
        self.velocity = Vec.unit(target - position) * self.config.BULLET_SPEED
        self.target = target
        self.created_at = created_at

    def move(self):
        self.position = self.position + self.velocity

    def is_reached_target(self):
        return Vec.distance(self.position, self.target) <= self.config.BULLET_SPEED


class Coin:
    def __init__(self, position: Vec):
        self.position = position
        self.radius = 10.0


class Game:
    def __init__(self, config: GameConfig):
        self.map = Map(config.TILES_HORIZONTAL_COUNT, config.TILES_VERTICAL_COUNT)
        self.tile_width = config.BOX_WIDTH / config.TILES_HORIZONTAL_COUNT
        self.tile_height = config.BOX_HEIGHT / config.TILES_VERTICAL_COUNT

        self.config = config
        self.players = [
            Player(player_id, Vec(random.randint(0, config.BOX_WIDTH), random.randint(0, config.BOX_HEIGHT)), config)
            for player_id in range(config.PLAYERS)
        ]

        self.bullets = []
        self.coin = self.create_coin()

        self.ticks = 0

    def tick(self, players_commands):
        moves = []
        shots = []
        dashes = []
        for client_id, command in players_commands.items():
            move, shot, dash = command
            if move is not None:
                moves.append(move)
            if shot is not None:
                shots.append(shot)
            if dash is not None:
                dashes.append(dash)

        # move player
        for move in moves:
            move.player.move(move.direction)

        # dashes
        # for dash in dashes:
        #     dash.player.dash(dash.direction)

        # coin
        coin_picked = False
        for player in self.players:
            if circles_collide(player.position, self.coin.position,
                               self.config.PLAYER_RADIUS, self.config.COIN_RADIUS):
                player.score += self.config.COIN_SCORE
                coin_picked = True
                break

        # player tile damage and timeouts
        teleport_players = set()
        for player_index in range(len(self.players)-1, -1, -1):
            player = self.players[player_index]
            player.timeouts()
            tile_x = int(player.position.x / self.tile_width)
            tile_y = int(player.position.y / self.tile_height)

            self.map.decrease(tile_x, tile_y, self.config.TILE_DECREASE_PER_TICK)
            if self.map.is_void(tile_x, tile_y):
                teleport_players.add(player)

        # move bullet and check player hit or target achievement
        for bullet_index in range(len(self.bullets)-1, -1, -1):
            bullet = self.bullets[bullet_index]
            bullet.move()

            for player_index in range(len(self.players)-1, -1, -1):
                player = self.players[player_index]
                if bullet.player != player and player.invulnerability_timeout == 0:
                    if circles_collide(bullet.position, player.position,
                                       self.config.BULLET_RADIUS, self.config.PLAYER_RADIUS):
                        bullet.player.score += 1
                        self.map.decrease(int(bullet.position.x / self.tile_width),
                                          int(bullet.position.y / self.tile_height),
                                          self.config.BULLET_TILE_DAMAGE)
                        self.bullets.pop(bullet_index)
                        teleport_players.add(player)
                        break
            else:
                if bullet.is_reached_target():
                    self.map.decrease(int(bullet.target.x / self.tile_width),
                                      int(bullet.target.y / self.tile_height),
                                      self.config.BULLET_TILE_DAMAGE)
                    self.bullets.pop(bullet_index)

        # all tile damage was done so we can teleport players who were hit by bullet
        top_tiles = self.map.top_tiles()
        for player in teleport_players:
            tile_x, tile_y = random.choice(top_tiles)
            player.position = Vec((0.5 + tile_x) * self.tile_width, (0.5 + tile_y) * self.tile_height)
            player.score -= self.config.TELEPORT_PENALTY

        if coin_picked or self.map.is_void(int(self.coin.position.x / self.tile_width),
                                           int(self.coin.position.y / self.tile_height)):
            self.coin = self.create_coin()

        for shot in shots:
            bullet = shot.player.shot(shot.point, self.ticks)
            if bullet is not None:
                self.bullets.append(bullet)

        self.ticks += 1

    def create_coin(self):
        free_tiles = set(self.map.unbroken_tiles())
        free_tiles -= set(
            (int(player.position.x / self.tile_width), int(player.position.y / self.tile_width))
            for player in self.players
        )
        free_tiles = list(free_tiles)
        x, y = random.choice(free_tiles)
        coin = Coin(Vec((x + 0.5) * self.tile_width, (y + 0.5) * self.tile_height))
        return coin

    def is_ended(self):
        return self.ticks == self.config.MAX_TICKS

    def get_player_by_id(self, player_id):
        for player in self.players:
            if player.id == player_id:
                return player

    def get_state(self):
        return {
            'ticks': self.ticks,
            'map': self.map.tiles,
            'players': [
                {
                    'id': player.id, 'position_x': player.position.x, 'position_y': player.position.y,
                    'bullet_count': player.bullet_count, 'bullet_reload_timeout': player.bullet_reload_timeout,
                    'invulnerability_timeout': player.invulnerability_timeout,
                    'blink_timeout': player.dash_timeout,
                    'shot_timeout': player.shot_timeout, 'score': player.score
                }
                for player in self.players
            ],
            'bullets': [
                {
                    'player_id': bullet.player.id, 'position_x': bullet.position.x, 'position_y': bullet.position.y,
                    'velocity_x': bullet.velocity.x, 'velocity_y': bullet.velocity.y
                }
                for bullet in self.bullets
            ],
            'coin': {
                'position_x': self.coin.position.x,
                'position_y': self.coin.position.y
            }
        }
