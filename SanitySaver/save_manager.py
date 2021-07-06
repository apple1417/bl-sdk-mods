from __future__ import annotations

import unrealsdk
import gzip
import json
import shutil
from pathlib import Path
from typing import Dict, IO, List, Union, cast

from .helpers import (DefDataTuple, expand_item_definition_data, expand_weapon_definition_data,
                      pack_item_definition_data, pack_weapon_definition_data,
                      unpack_item_definition_data, unpack_weapon_definition_data)

STASH_NAME = "Stash"

_COMPRESS = True

_SAVES_DIR = Path(__file__).parent / "Saves"
_SAVES_DIR.mkdir(exist_ok=True)


ItemData = Dict[str, Union[str, int, None]]
ItemDataDict = Dict[int, List[ItemData]]


def update_compression(should_compress: bool) -> None:
    """
    Changes if the save managers will gzip their files, and updates any existing files to the
    correct format.
    """
    global _COMPRESS
    _COMPRESS = should_compress

    for file in _SAVES_DIR.glob("*.json" if should_compress else "*.json.gz"):
        json_mode = "rb" if should_compress else "wb"
        gz_mode = "wb" if should_compress else "rb"

        # Hacky way to remove just the suffixes we care about
        suffixes = list(file.suffixes)
        if suffixes[-1] == ".gz":
            suffixes.pop()
        if suffixes[-1] == ".json":
            suffixes.pop()
        base_file = file.parent / (file.stem.split(".")[0] + "".join(suffixes))

        with open(base_file.with_suffix(".json"), json_mode) as js:  # noqa: SIM117
            with gzip.open(base_file.with_suffix(".json.gz"), gz_mode) as gz:
                if should_compress:
                    shutil.copyfileobj(js, gz)
                else:
                    shutil.copyfileobj(gz, js)
        file.unlink()


class SaveManager:
    """
    Class that deals with our custom item saving. By default sets up an empty save, call `load()`
    first to load from file (if it exists).

    All items have a `UniqueId` field, which we use to uniquely identify them. In the rare case
    there's a conflict, we'll go in the order they're stored. Gibbed's editor changes unique id on
    import so this should be exceedingly .

    We split our custom save format into two parts:
    1. A dict mapping unique ids to parts to replace. Replacements are minimal, only what the game
    won't save for us (allowing changing the rest with a normal save editor).
    2. A dict mapping unique idsto full dumps of the parts for new weapons - ones we haven't seen go
       through a sq yet, so we don't know what the minimal replacements are.
    """
    file_path: Path

    replacements: ItemDataDict
    new_items: ItemDataDict

    def __init__(self, save_name: str, is_bank: bool = False) -> None:
        file_name = Path(save_name).stem + ("_Bank" if is_bank else "")
        extension = ".json" + (".gz" if _COMPRESS else "")
        self.file_path = _SAVES_DIR / Path(file_name).with_suffix(extension)

        self.replacements = {}
        self.new_items = {}

    def load(self) -> None:
        """
        Loads all save data from disk, or loads empty save data if the file does not exist or is
        malformed.
        """
        try:
            file: IO[str]
            if _COMPRESS:
                file = gzip.open(self.file_path, "rt", encoding="utf8")
            else:
                file = open(self.file_path)  # noqa: SIM115

            data = json.load(file)
            # JSON doesn't allow int keys, dumping converts them to strings, we need to convert back
            self.replacements = {
                int(unique_id): val for unique_id, val in data.get("replacements", {}).items()
            }
            self.new_items = {
                int(unique_id): val for unique_id, val in data.get("new_items", {}).items()
            }
            file.close()

        # In this version of python, gzip throws base `OSError`s, which also catches file not founds
        except (OSError, json.JSONDecodeError):
            self.replacements = {}
            self.new_items = {}

    def write(self) -> None:
        """ Writes all save data to disk, overwriting existing files. """
        # Clear out empty categories first
        for item_dict in (self.new_items, self.replacements):
            to_remove = set()
            for unique_id, val in item_dict.items():
                if len(val) <= 0:
                    to_remove.add(unique_id)
            for unique_id in to_remove:
                item_dict.pop(unique_id)

        file: IO[str]
        if _COMPRESS:
            file = gzip.open(self.file_path, "wt", encoding="utf8")
        else:
            file = open(self.file_path, "w")  # noqa: SIM115

        json.dump({
            "replacements": self.replacements,
            "new_items": self.new_items
        }, file, indent=None if _COMPRESS else 4)

        file.close()

    def add_item(self, item: unrealsdk.FStruct, is_weapon: bool, existing_save: SaveManager) -> None:
        """
        Adds a new item from it's definition data struct.

        To update the stored items, you're expected to use two `SaveManager` objects. One to load
        the existing save, and one to write the new one into. This function expects to be run on the
        new object and have the the existing one be passed into it.
        """
        replacements = existing_save.replacements.get(item.UniqueId, [])
        if len(replacements) > 0:
            if item.UniqueId not in self.replacements:
                self.replacements[item.UniqueId] = []
            self.replacements[item.UniqueId].append(replacements.pop(0))
            return

        # If an item is already in new on the existing save, this just puts it back in there
        self._add_new_item(item, is_weapon)

    def apply_replacements(self, item: unrealsdk.FStruct, is_weapon: bool) -> DefDataTuple:
        """
        Takes a definition data struct and returns a tuple of it with any replacements applied. Also
        updates our internal representation of the save the information about what parts get deleted
        that we learn.
        """
        # Prefer reading items out of replacements if possible
        replacements = self.replacements.get(item.UniqueId, [])
        if len(replacements) > 0:
            current_parts: ItemData
            if is_weapon:
                current_parts = pack_weapon_definition_data(item)
            else:
                current_parts = pack_item_definition_data(item)

            """
            Move the replacement we're using to the end of the list, so the next call with the same
            unique id gets the next replacement.
            We can't just pop it like everywhere else cause we still need to save it.
            """
            first_replacement = replacements.pop(0)
            replacements.append(first_replacement)

            current_parts.update(first_replacement)
            if is_weapon:
                return unpack_weapon_definition_data(current_parts)
            else:
                return unpack_item_definition_data(current_parts)

        # Next check if it's in new items instead, and convert it into a replacement
        new_items = self.new_items.get(item.UniqueId, [])
        if len(new_items) > 0:
            known_parts = new_items.pop(0)
            self._create_replacement_from_new(item, is_weapon, known_parts)

            # Return our complete stored dict
            known_parts["UniqueId"] = item.UniqueId
            if is_weapon:
                return unpack_weapon_definition_data(known_parts)
            else:
                return unpack_item_definition_data(known_parts)

        # If we haven't seen an item before, don't change anything, and add it to our save if needed
        self._add_new_item(item, is_weapon)
        if is_weapon:
            return expand_weapon_definition_data(item)
        else:
            return expand_item_definition_data(item)

    def _add_new_item(self, item: unrealsdk.FStruct, is_weapon: bool) -> None:
        # Doing this a little weird to try coerce the description to the top of the json dumps
        packed: ItemData = {}
        self._add_description(item, is_weapon, packed)
        if is_weapon:
            packed.update(pack_weapon_definition_data(item))
        else:
            packed.update(pack_item_definition_data(item))

        unique_id = cast(int, packed.pop("UniqueId"))
        if unique_id not in self.new_items:
            self.new_items[unique_id] = []
        self.new_items[unique_id].append(packed)

    def _create_replacement_from_new(self, item: unrealsdk.FStruct, is_weapon: bool, known_parts: ItemData) -> None:
        engine = unrealsdk.GetEngine()

        replacements: ItemData = {}
        self._add_description(item, is_weapon, replacements)
        for field, val in known_parts.items():
            actual_val = getattr(item, field)
            if isinstance(actual_val, unrealsdk.UObject):
                actual_val = engine.PathName(actual_val)
            if actual_val != val:
                replacements[field] = val

        if item.UniqueId not in self.replacements:
            self.replacements[item.UniqueId] = []
        self.replacements[item.UniqueId].append(replacements)

    def _add_description(self, item: unrealsdk.FStruct, is_weapon: bool, item_data: ItemData) -> None:
        description = []
        if item.ManufacturerGradeIndex is not None:
            description.append(f"Level {item.ManufacturerGradeIndex}")
        if is_weapon:
            if item.PrefixPartDefinition is not None:
                description.append(item.PrefixPartDefinition.PartName)
            if item.TitlePartDefinition is not None:
                description.append(item.TitlePartDefinition.PartName)
        else:
            if item.PrefixItemNamePartDefinition is not None:
                description.append(item.PrefixItemNamePartDefinition.PartName)
            if item.TitleItemNamePartDefinition is not None:
                description.append(item.TitleItemNamePartDefinition.PartName)
        if len(description) > 0:
            item_data["_description"] = " ".join(x for x in description if x is not None)
