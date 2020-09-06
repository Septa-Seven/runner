from utils import Vec


class InvalidAction(Exception):
    pass


def parse_command(game, player_id, command):
    # print('COMMAND', command)
    try:
        move = Direction(**command['move'], game=game, player_id=player_id)
    except (KeyError, TypeError, InvalidAction):
        move = None

    try:
        shot = Direction(**command['shot'], game=game, player_id=player_id)
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
