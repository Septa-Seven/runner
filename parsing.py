from __future__ import annotations

from typing import Tuple, Optional

import config
from game.game import Game
from game.utils import Vec, is_outside_box
from exceptions import InvalidAction


def parse_command(game: Game, player_id: int, command: dict) -> Tuple[Optional[Move], Optional[Shot]]:
    try:
        move = Move(**command['move'], game=game, player_id=player_id)
    except (KeyError, TypeError, InvalidAction):
        move = None

    try:
        shot = Shot(**command['shot'], game=game, player_id=player_id)
    except (KeyError, TypeError, InvalidAction):
        shot = None

    return move, shot


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

        if is_outside_box(point_x, point_y, config.global_config.box_width, config.global_config.box_height):
            raise InvalidAction

        self.point = Vec(point_x, point_y)


class Move(Direction):
    def apply(self):
        self.player.move(self.direction)


class Shot(Point):
    def apply(self, tick):
        return self.player.shot(self.point, tick)
