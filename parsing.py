from __future__ import annotations

from typing import Tuple, Optional

import config
from game.game import Game
from game.utils import Vec, is_outside_box
from exceptions import InvalidAction


def parse_command(game: Game, player_id: int, command: dict) -> \
        Tuple[Optional[Move], Optional[Dash], Optional[Shot], Optional[Boolean]]:
    try:
        move = Move(**command['move'], game=game, player_id=player_id)
    except (KeyError, TypeError, InvalidAction):
        move = None

    try:
        shot = Shot(**command['shot'], game=game, player_id=player_id)
    except (KeyError, TypeError, InvalidAction):
        shot = None

    try:
        pick_weapon = Boolean(game, player_id, command['pick_weapon'])
    except (KeyError, TypeError, InvalidAction):
        pick_weapon = None

    try:
        dash = Dash(game, player_id, command['dash'])
    except (KeyError, TypeError, InvalidAction):
        dash = None

    return move, dash, shot, pick_weapon


class Action:
    def __init__(self, game: Game, player_id: int):
        self.player = game.get_player_by_id(player_id)

    def apply(self, *args, **kwargs):
        raise NotImplemented


class Direction(Action):
    def __init__(self, direction_x, direction_y, *args, **kwargs):
        if not isinstance(direction_x, (int, float)) or not isinstance(direction_y, (int, float)):
            raise InvalidAction

        self.direction = Vec(direction_x, direction_y)
        super().__init__(*args, **kwargs)


class Point(Action):
    def __init__(self, game, player_id, point_x, point_y):
        if not isinstance(point_x, (int, float)) or not isinstance(point_y, (int, float)):
            raise InvalidAction

        super().__init__(game, player_id)

        if is_outside_box(point_x, point_y, config.global_config.arena_width, config.global_config.arena_height):
            raise InvalidAction

        self.point = Vec(point_x, point_y)


class Boolean(Action):
    def __init__(self, game, player_id, value):
        if not isinstance(value, bool) or value is not True:
            raise InvalidAction

        super().__init__(game, player_id)


class Move(Direction):
    def apply(self):
        self.player.set_direction(self.direction)


class Shot(Point):
    def apply(self, tick):
        return self.player.shot(self.point, tick)


class Dash(Boolean):
    def apply(self):
        return self.player.perform_dash()
