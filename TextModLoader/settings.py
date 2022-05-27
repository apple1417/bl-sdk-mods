import json
from typing import Optional, Set

from Mods.TextModLoader.constants import (JSON, SETTINGS_AUTO_ENABLE, SETTINGS_FILE,
                                          SETTINGS_MOD_INFO, SETTINGS_VERSION, VERSION)


def load_auto_enable() -> Set[str]:
    """
    Loads the list of enabled mods stored in the settings file.

    Returns:
        A set of auto enabling mod filenames.
    """
    try:
        with open(SETTINGS_FILE) as file:
            return set(json.load(file)[SETTINGS_AUTO_ENABLE])
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return set()


def load_mod_info() -> JSON:
    """
    Loads the mod info stored in the settings file.

    Returns:
        The JSON formatted settings.
    """
    try:
        with open(SETTINGS_FILE) as file:
            settings = json.load(file)

            # Force everything to be reloaded if the mod version changes, in either direction
            if settings[SETTINGS_VERSION] != list(VERSION):
                return {}

            return settings[SETTINGS_MOD_INFO]  # type: ignore
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return {}


def dump_settings(
    auto_enable: Optional[Set[str]] = None,
    mod_info: Optional[JSON] = None,
) -> None:
    """
    Updates the current settings file with the passed data. Leave an arg as None to not touch it, to
     keep the currently stored version.

    Always updates the stored version.

    Args:
        auto_enable: The set of auto enabling mod filenames.
        mod_info: The JSON mod info data.
    """
    settings: JSON = {}
    try:
        with open(SETTINGS_FILE) as file:
            settings = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    if mod_info is not None:
        settings[SETTINGS_MOD_INFO] = mod_info
    if auto_enable is not None:
        settings[SETTINGS_AUTO_ENABLE] = sorted(auto_enable)
    settings[SETTINGS_VERSION] = VERSION

    with open(SETTINGS_FILE, "w") as file:
        json.dump(settings, file, indent=4, sort_keys=True)
