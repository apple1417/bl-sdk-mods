import sys
from os import path
from typing import Any, Dict, Tuple

from Mods.ModMenu import Game

VERSION: Tuple[int, int] = (1, 1)

JSON = Dict[str, Any]

TEXT_MOD_PRIORITY: int = -5

BINARIES_DIR: str = path.abspath(path.join(path.dirname(sys.executable), ".."))

BLCMM_GAME_MAP: Dict[str, Game] = {
    "bl2": Game.BL2,
    "tps": Game.TPS
}

META_TAG_TITLE: str = "@title"
META_TAG_AUTHOR: str = "@author"
META_TAG_MAIN_AUTHOR: str = "@main-author"
META_TAG_VERSION: str = "@version"
META_TAG_DESCRIPTION: str = "@description"
META_TAG_TML_PRIORITY: str = "@tml-priority"
META_TAG_TML_IGNORE_ME: str = "@tml-ignore-me"

SETTINGS_FILE: str = path.abspath(path.join(path.dirname(__file__), "mod_info.json"))
SETTINGS_VERSION: str = "tml_version"
SETTINGS_MOD_INFO: str = "mod_info"
SETTINGS_AUTO_ENABLE: str = "auto_enable"

SETTINGS_IS_MOD_FILE: str = "is_mod_file"
SETTINGS_MODIFY_TIME: str = "modify_time"
SETTINGS_SPARK_SERVICE_IDX: str = "spark_service_idx"
SETTINGS_RECOMMENDED_GAME: str = "recommended_game"
SETTINGS_META: str = "metadata"
