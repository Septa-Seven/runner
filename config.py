class GameConfig:
    __slots__ = (
        "players", "max_ticks",
        "items",
        "box_width", "box_height",
        "bullet_radius", "bullet_speed",
        "player_radius", "player_speed",
        "max_bullets",
        "shot_timeout", "reload_timeout", "invulnerability_timeout",
        "hit_score",
        "item_radius",
        "boots_speed_effect",
        "mask_hit_score_effect",
        "pocket_max_bullets_effect",
        "dragon_shot_timeout_effect",
        "leaf_reload_timeout_effect"
    )

    def __init__(self, json_data):
        for slot_name in self.__slots__:
            setattr(self, slot_name, json_data[slot_name])

    def __str__(self):
        return '\n'.join(f'{attr}: {self.__getattribute__(attr)}' for attr in self.__slots__)

    def json(self):
        return {key: getattr(self, key, None) for key in self.__slots__}


global_config = None


def set_global_config(config: GameConfig):
    global global_config
    global_config = config
