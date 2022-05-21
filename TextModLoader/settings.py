import json

from Mods.TextModLoader.constants import JSON, SETTINGS_FILE


def load_settings_file() -> JSON:
    """
    Loads the data stored in the settings file.

    Returns:
        The JSON formatted settings.
    """
    settings: JSON = {}
    try:
        with open(SETTINGS_FILE) as file:
            settings = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return settings


def dump_settings_file(settings: JSON) -> None:
    """
    Dumps JSON formatted settings to the settings file.

    Args:
        settings: The JSON settings data.
    """
    with open(SETTINGS_FILE, "w") as file:
        json.dump(settings, file, indent=4, sort_keys=True)
