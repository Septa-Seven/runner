class GameConfig:
    __slots__ = (
        "execution_timeout",
        "response_timeout",
        "command_size_limit",
        "players", "max_ticks",
        "items",
        "item_radius",
        "chainsaws",
        "chainsaw_radius",
        "chainsaw_speed",
        "arena_width", "arena_height",
        "bullet_radius", "bullet_speed",
        "player_radius", "player_speed",
        "max_bullets",
        "shot_timeout", "reload_timeout",
        "drop_out_invulnerability_timeout",
        "hit_score",
        "boots_speed_effect",
        "mask_hit_score_increment",
        "ammunition_max_bullets_effect",
        "ammunition_shot_timeout_effect",
        "ammunition_reload_timeout_effect",
        "dash_duration", "dash_speed_bonus", "dash_cooldown",

        "shotgun_hit_score",
        "shotgun_max_bullets",
        "shotgun_reload_timeout",
        "shotgun_shot_timeout",
        "shotgun_bullet_speed",
        "shotgun_shot_offset",

        "sniper_rifle_hit_score",
        "sniper_rifle_max_bullets",
        "sniper_rifle_reload_timeout",
        "sniper_rifle_shot_timeout",
        "sniper_rifle_bullet_speed",
        "sniper_rifle_shot_offset",

        "pistol_hit_score",
        "pistol_max_bullets",
        "pistol_reload_timeout",
        "pistol_shot_timeout",
        "pistol_bullet_speed",
        "pistol_shot_offset"
    )

    def __init__(self, json_data):
        for slot_name in self.__slots__:
            setattr(self, slot_name, json_data[slot_name])

    def __str__(self):
        return '\n'.join(f'{attr}: {self.__getattribute__(attr)}' for attr in self.__slots__)

    def json(self):
        return {key: getattr(self, key) for key in self.__slots__}


global_config = None


def set_global_config(config: GameConfig):
    global global_config
    global_config = config
