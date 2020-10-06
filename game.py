from utils import circles_collide, point_in_circle, Vec, is_outside_box
from config import GameConfig


# TODO rename constants
class Player:
    def __init__(self, id: int, position: Vec, config: GameConfig):
        self.config = config

        self.id = id
        self.position = position
        self.spawn = position
        self.score = 0

        self.bullet_reload_timeout = self.config.bullet_reload_timeout
        self.bullet_count = self.config.max_bullets
        self.invulnerability_timeout = 0
        self.shot_timeout = 0

    def move(self, direction: Vec):
        self.position = self.position + direction * self.config.player_speed

        # player can't move outside the box
        self.position.x = max(0.0, min(self.position.x, self.config.box_width - 1))
        self.position.y = max(0.0, min(self.position.y, self.config.box_height - 1))

    def timeouts(self):
        if self.shot_timeout > 0:
            self.shot_timeout -= 1

        if self.invulnerability_timeout > 0:
            self.invulnerability_timeout -= 1

        if self.bullet_count < self.config.max_bullets:
            self.bullet_reload_timeout -= 1

            if self.bullet_reload_timeout == 0:
                self.bullet_count += 1
                self.bullet_reload_timeout = self.config.bullet_reload_timeout

    def shot(self, target: Vec, tick: int):
        if (self.bullet_count > 0
                and self.shot_timeout == 0
                and self.invulnerability_timeout == 0):
            self.bullet_count -= 1
            self.shot_timeout = self.config.shot_timeout
            return Bullet(self, self.position, target, tick, self.config)

    def to_spawn(self):
        self.position = self.spawn
        self.invulnerability_timeout = self.config.invulnerability_timeout


class Bullet:
    def __init__(self, player: Player, position: Vec, target: Vec, created_at: int, config: GameConfig):
        self.config = config
        self.player = player
        self.position = position
        self.velocity = Vec.unit(target - position) * self.config.bullet_speed
        self.target = target
        self.created_at = created_at

    def move(self):
        self.position = self.position + self.velocity


class Crown:
    def __init__(self, position: Vec):
        self.position = position
        self.player = None

    def tick(self):
        if self.player is not None:
            self.player.score += 1


class Game:
    def __init__(self, config: GameConfig):
        self.config = config
        self.players = [
            Player(spawn['player_id'], Vec(spawn['spawn_x'], spawn['spawn_y']), config)
            for spawn in config.spawns
        ]

        self.bullets = []
        self.crown = Crown(Vec(self.config.box_width/2, self.config.box_height/2))

        self.ticks = 0

    def tick(self, players_commands):
        moves = []
        shots = []
        for client_id, command in players_commands.items():
            move, shot = command
            if move is not None:
                moves.append(move)
            if shot is not None:
                shots.append(shot)

        # move player
        for move in moves:
            move.player.move(move.direction)

        # player timeouts
        for player in self.players:
            player.timeouts()

        # check crown collisions
        if self.crown.player is None:
            for player in self.players:
                if circles_collide(player.position, self.crown.position,
                                   self.config.player_radius, self.config.crown_radius):
                    # crown can't be picked up when it collides with multiple players
                    if self.crown.player is None:
                        self.crown.player = player
                    else:
                        self.crown.player = None
                        break

        # crown score
        self.crown.tick()

        # move or delete bullet and check player hit
        for bullet_index in range(len(self.bullets)-1, -1, -1):
            bullet = self.bullets[bullet_index]
            if is_outside_box(bullet.position.x, bullet.position.y,
                              self.config.box_width, self.config.box_height):
                del self.bullets[bullet_index]
                continue

            bullet.move()

            for player_index in range(len(self.players)-1, -1, -1):
                player = self.players[player_index]
                if bullet.player != player and player.invulnerability_timeout == 0:
                    if circles_collide(bullet.position, player.position,
                                       self.config.bullet_radius, self.config.player_radius):
                        bullet.player.score += self.config.hit_score

                        # crown drop
                        if self.crown.player == player:
                            self.crown.position = self.crown.player.position
                            self.crown.player = None

                        player.to_spawn()

                        del self.bullets[bullet_index]
                        break

        for shot in shots:
            bullet = shot.player.shot(shot.point, self.ticks)
            if bullet is not None:
                self.bullets.append(bullet)

        self.ticks += 1

    def is_ended(self):
        return self.ticks == self.config.max_ticks

    def get_player_by_id(self, player_id):
        for player in self.players:
            if player.id == player_id:
                return player

    def get_state(self):
        return {
            'ticks': self.ticks,
            'players': [
                {
                    'id': player.id, 'position_x': player.position.x, 'position_y': player.position.y,
                    'bullet_count': player.bullet_count, 'bullet_reload_timeout': player.bullet_reload_timeout,
                    'invulnerability_timeout': player.invulnerability_timeout,
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
            'crown': {
                'player_id': None, 'position_x': self.crown.position.x, 'position_y': self.crown.position.y
            } if self.crown.player is None else {
                'player_id': self.crown.player.id, 'position_x': self.crown.player.position.x,
                'position_y': self.crown.player.position.y
            }
        }
