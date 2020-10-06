class GameConfig:
    __slots__ = (
        "players", "spawns", "max_ticks",
        "box_width", "box_height",
        "bullet_radius", "bullet_speed", "player_radius",
        "player_speed", "max_bullets",
        "shot_timeout", "bullet_reload_timeout",
        "invulnerability_timeout", "crown_radius",
        "hit_score"
    )

    def __init__(self, json_data):
        for slot_name in self.__slots__:
            setattr(self, slot_name, json_data[slot_name])

    def __str__(self):
        return '\n'.join(f'{attr}: {self.__getattribute__(attr)}' for attr in self.__slots__)

    def json(self):
        return {key: getattr(self, key, None) for key in self.__slots__}
