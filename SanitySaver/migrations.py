import unrealsdk
import traceback
from typing import Any, Callable, List

from .compression_handler import dump, load
from .save_manager import _SAVES_DIR, SAVE_VERSION, SAVE_VERSION_KEY


def _migrate_v1(data: Any) -> Any:
    all_items = {}
    for unique_id, part_list in data["replacements"].items():
        if len(part_list) > 1:
            raise RuntimeError(f"Multiple items have the same unique id {unique_id}")
        elif len(part_list) == 1:
            all_items[unique_id] = part_list[0]

    for unique_id, part_list in data["new_items"].items():
        if len(part_list) > 1:
            raise RuntimeError(f"Multiple items have the same unique id {unique_id}")
        elif len(part_list) == 1:
            all_items[unique_id] = part_list[0]
            all_items[unique_id]["_inital"] = True

    return {
        SAVE_VERSION_KEY: 2,
        "items": all_items
    }


MIGRATION_FUNCTIONS: List[Callable[[Any], Any]] = [
    _migrate_v1
]


def migrate_all() -> None:
    """ Migrates saves from older versions of Sanity Saver up to the current one. """
    for file in _SAVES_DIR.iterdir():
        if not file.is_file():
            continue

        data = load(file)

        version: int
        try:
            version = data[SAVE_VERSION_KEY]
        except KeyError:
            version = 1

        if version >= SAVE_VERSION:
            continue

        original_data = data
        try:
            for i in range(version, SAVE_VERSION):
                data = MIGRATION_FUNCTIONS[i - 1](data)
        except Exception:
            # I don't want to require UserFeedback just to show this error message
            # It would simplify this a bit to just:
            #   `TrainingBox("Sanity Saver", f"Failed...", PausesGame=True).Show()`
            unrealsdk.GetEngine().GamePlayers[0].Actor.GFxUIManager.ShowTrainingDialog(
                f"Failed to migrate save {file.name}. It has been moved to a backup location.",
                "Sanity Saver",
                0,
                0,
                False
            ).ApplyLayout()

            unrealsdk.Log(f"[Sanity Saver] Exception thrown while migrating {file.name}:")
            for line in traceback.format_exc().split("\n"):
                unrealsdk.Log(line)

            (_SAVES_DIR / "Backup").mkdir(exist_ok=True)
            dump(original_data, _SAVES_DIR / "Backup" / file.name)
            file.unlink()
            continue

        dump(data, file)
