class GameConfig:
    __slots__ = (
        'PLAYERS', 'MAX_TICKS', 'BOX_WIDTH', 'BOX_HEIGHT',
        'BULLET_RADIUS', 'BULLET_SPEED',
        'PLAYER_RADIUS', 'PLAYER_SPEED', 'MAX_BULLETS',
        'SHOT_TIMEOUT', 'BULLET_RELOAD_TIMEOUT', 'INVULNERABILITY_TIMEOUT',
        'BLINK_RADIUS', 'BLINK_TIMEOUT', 'TILES_HORIZONTAL_COUNT',
        'TILES_VERTICAL_COUNT', 'BULLET_TILE_DAMAGE',
        'TILE_DECREASE_PER_TICK', 'TELEPORT_PENALTY',
        'COIN_RADIUS', 'COIN_SCORE'
    )

    def __init__(self, json_data):
        for slot_name in self.__slots__:
            setattr(self, slot_name, json_data[slot_name])

    def __str__(self):
        return '\n'.join(f'{attr}: {self.__getattribute__(attr)}' for attr in self.__slots__)

    def json(self):
        return {key: getattr(self, key, None) for key in self.__slots__}
