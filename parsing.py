from utils import Vec, is_outside_box


class InvalidAction(Exception):
    pass


def parse_command(game, player_id, command):
    # print('COMMAND', command)
    try:
        move = Direction(**command['move'], game=game, player_id=player_id)
    except (KeyError, TypeError, InvalidAction):
        move = None

    try:
        shot = Point(**command['shot'], game=game, player_id=player_id)
    except (KeyError, TypeError, InvalidAction):
        shot = None

    try:
        blink = Direction(**command['blink'], game=game, player_id=player_id)
    except (KeyError, TypeError, InvalidAction):
        blink = None

    return move, shot, blink


class Action:
    def __init__(self, game, player_id):
        self.player = game.get_player_by_id(player_id)


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

        if is_outside_box(point_x, point_y, game.config.BOX_WIDTH, game.config.BOX_HEIGHT):
            raise InvalidAction

        self.point = Vec(point_x, point_y)
