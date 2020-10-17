from __future__ import annotations
from utils import circles_collide, Vec, is_outside_box
import config
from items import Item, Tickable
from exceptions import ShotError
from timer import Timer


class Player:
    def __init__(self, id: int, position: Vec):
        # modifiers
        self.speed = config.global_config.player_speed
        self.hit_score = config.global_config.hit_score
        self.max_bullets = config.global_config.max_bullets
        self.reload_timeout = config.global_config.reload_timeout
        self.shot_timeout = config.global_config.shot_timeout

        self.id = id
        self.position = position
        self.score = 0
        self.bullet_count = self.max_bullets

        self.reload_timer = Timer()
        self.reload_timer.set(self.reload_timeout)

        self.invulnerability_timer = Timer()
        self.shot_timer = Timer()

    def move(self, direction: Vec):
        self.position = self.position + Vec.unit(direction) * self.speed

        # player can't move outside the box
        self.position.x = max(0.0, min(self.position.x, config.global_config.box_width))
        self.position.y = max(0.0, min(self.position.y, config.global_config.box_height))

    def timeouts(self):
        self.shot_timer.tick()
        self.invulnerability_timer.tick()

        if self.bullet_count < self.max_bullets:
            self.reload_timer.tick()

            if self.reload_timer.ready():
                self.bullet_count += 1
                self.reload_timer.set(self.reload_timeout)

    def shot(self, target: Vec, tick: int) -> Bullet:
        if (self.bullet_count == 0
                or not self.invulnerability_timer.ready()
                or not self.shot_timer.ready()):
            raise ShotError

        self.bullet_count -= 1
        self.shot_timer.set(self.shot_timeout)
        return Bullet(self, self.position, target, tick)


class Bullet:
    def __init__(self, player: Player, position: Vec, target: Vec, created_at: int):
        self.player = player
        self.position = position
        self.velocity = Vec.unit(target - position) * config.global_config.bullet_speed
        self.created_at = created_at

    def move(self):
        self.position = self.position + self.velocity


class Game:
    def __init__(self):
        self.players = [
            Player(player['id'], Vec(player['position_x'], player['position_y']))
            for player in config.global_config.players
        ]

        self.bullets = []
        item_cls_mapping = Item.mapping()
        self.items = [
            item_cls_mapping[item['id']](Vec(item['spawn_x'], item['spawn_y']))
            for item in config.global_config.items
        ]

        self.ticks = 0

    def tick(self, commands):
        moves = []
        shots = []
        for command in commands:
            move, shot = command
            if move is not None:
                moves.append(move)
            if shot is not None:
                shots.append(shot)

        for move_action in moves:
            move_action.apply()

        for player in self.players:
            player.timeouts()

        # check item collisions
        for item in self.items:
            if item.player is None:
                for player in self.players:
                    if (player.invulnerability_timer.ready()
                            and circles_collide(player.position, item.spawn,
                                                config.global_config.player_radius,
                                                config.global_config.item_radius)):
                        # item can't be picked up when it collides with multiple players
                        if item.player is None:
                            item.pick(player)
                        else:
                            item.drop()
                            break

        for item in self.items:
            if isinstance(item, Tickable):
                item.tick()

        for bullet_index in range(len(self.bullets)-1, -1, -1):
            bullet = self.bullets[bullet_index]
            if is_outside_box(bullet.position.x, bullet.position.y,
                              config.global_config.box_width,
                              config.global_config.box_height):
                del self.bullets[bullet_index]
                continue

            bullet.move()

            for player in self.players:
                if (bullet.player != player
                        and player.invulnerability_timer.ready()
                        and circles_collide(bullet.position, player.position,
                                            config.global_config.bullet_radius,
                                            config.global_config.player_radius)):

                    for item in self.items:
                        if item.player == player:
                            item.drop()

                    player.invulnerability_timer.set(config.global_config.invulnerability_timeout)

                    bullet.player.score += bullet.player.hit_score
                    del self.bullets[bullet_index]

                    break

        for shot_action in shots:
            try:
                bullet = shot_action.apply(self.ticks)
            except ShotError:
                continue
            else:
                self.bullets.append(bullet)

        self.ticks += 1

    def is_ended(self):
        return self.ticks == config.global_config.max_ticks

    def get_player_by_id(self, player_id):
        for player in self.players:
            if player.id == player_id:
                return player

    def get_state(self):
        return {
            'ticks': self.ticks,
            'players': [
                {
                    'id': player.id,
                    'score': player.score,
                    'speed': player.speed,
                    'hit_score': player.hit_score,
                    'position_x': player.position.x, 'position_y': player.position.y,
                    'bullet_count': player.bullet_count,
                    'reload_timeout': player.reload_timer.ticks,
                    'shot_timeout': player.shot_timer.ticks,
                    'invulnerability_timeout': player.invulnerability_timer.ticks,
                }
                for player in self.players
            ],
            'bullets': [
                {
                    'player_id': bullet.player.id,
                    'position_x': bullet.position.x, 'position_y': bullet.position.y,
                    'velocity_x': bullet.velocity.x, 'velocity_y': bullet.velocity.y
                }
                for bullet in self.bullets
            ],
            'items': [
                {
                    'id': item.id,
                    'player_id': None if item.player is None else item.player.id,
                    'spawn_x': item.spawn.x,
                    'spawn_y': item.spawn.y,
                }
                for item in self.items
            ]
        }
