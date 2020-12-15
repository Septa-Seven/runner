from typing import get_origin, get_args
from game.utils import Vec


class ConfigError(Exception):
    pass


def restricted_typing(value, expected_type):
    if get_origin(expected_type) == list:
        (expected_item_type,) = get_args(expected_type)
        value = [restricted_typing(item, expected_item_type) for item in value]
    elif issubclass(expected_type, (ObjectConfig, Vec)):
        value = expected_type(**value)
    elif not isinstance(value, (int, float, str)):
        raise ConfigError(f'Wrong value type for {value}. Expected {expected_type} but got {type(value)}')

    return value


class ObjectConfig:
    def __init__(self, **kwargs):
        for name, expected_type in self.__annotations__.items():
            setattr(self, name, restricted_typing(kwargs[name], expected_type))


class RestrictionsConfig(ObjectConfig):
    execution_timeout: float
    response_timeout: float
    command_size_limit: int
    max_ticks: int


class WeaponConfig(ObjectConfig):
    hit_score: int
    initial_bullets: int
    shot_timeout: int
    shot_offset: float
    bullet_speed: float


class WeaponsConfig(ObjectConfig):
    bullet_radius: float

    pistol: WeaponConfig
    sniper_rifle: WeaponConfig
    shotgun: WeaponConfig


class ArenaConfig(ObjectConfig):
    width: float
    height: float
    item_spawn_period: int
    item_radius: float


class DashConfig(ObjectConfig):
    duration: int
    cooldown: int
    speed_bonus: float


class PlayerInitialData(ObjectConfig):
    id: int
    position: Vec


class PlayersConfig(ObjectConfig):
    radius: float
    speed: float
    drop_out_invulnerability_timeout: int
    dash: DashConfig

    initial: list[PlayerInitialData]


class ChainsawConfig(ObjectConfig):
    radius: float
    speed: float

    path: list[Vec]


class CrownConfig(ObjectConfig):
    spot: Vec


class GameConfig(ObjectConfig):
    restrictions: RestrictionsConfig
    arena: ArenaConfig
    weapons: WeaponsConfig
    players: PlayersConfig
    chainsaws: list[ChainsawConfig]
    crown: CrownConfig

    def __init__(self, **kwargs):
        self.raw_config = kwargs
        super().__init__(**kwargs)


global_config: GameConfig = None


def set_global_config(config: GameConfig):
    global global_config
    global_config = config
