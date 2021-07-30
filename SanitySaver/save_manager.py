from __future__ import annotations

import unrealsdk
import json
import random
from pathlib import Path
from typing import ClassVar, Dict, Union, cast

from .compression_handler import delete, dump, load
from .helpers import (DefDataTuple, expand_item_definition_data, expand_weapon_definition_data,
                      pack_item_definition_data, pack_weapon_definition_data,
                      unpack_item_definition_data, unpack_weapon_definition_data)

SAVE_VERSION: int = 2
SAVE_VERSION_KEY: str = "save_version"

_SAVES_DIR = Path(__file__).parent / "Saves"
_SAVES_DIR.mkdir(exist_ok=True)

STASH_NAME: str = "Stash"


ItemData = Dict[str, Union[str, int, None]]
ItemDataDict = Dict[int, ItemData]


class SaveManager:
    """
    Class that deals with our custom item saving. By default sets up an empty save, call `load()`
    first to load from file (if it exists).

    All items have a `UniqueId` field, which we use to uniquely identify them. In the rare case
    there's a conflict, we can just change the id. There's an issue in gibbed's editor which means
    this isn't quite a 1/2^32 we can ignore:
    https://github.com/gibbed/Gibbed.Borderlands2/issues/154
    """
    file_path: Path

    items: ItemDataDict
    ITEMS_KEY: ClassVar[str] = "items"

    def __init__(self, save_name: str, is_bank: bool = False) -> None:
        file_name = Path(save_name).stem + ("_Bank" if is_bank else "") + ".json"
        self.file_path = _SAVES_DIR / Path(file_name)

        self.items = {}

    def load(self) -> None:
        """
        Loads all save data from disk, or loads empty save data if the file does not exist or is
        malformed.
        """
        try:
            data = load(self.file_path)
            # JSON doesn't allow int keys, dumping converts them to strings, we need to convert back
            self.items = {
                int(unique_id): val for unique_id, val in data.get(self.ITEMS_KEY, {}).items()
            }

        except (OSError, json.JSONDecodeError):
            self.items = {}

    def write(self) -> None:
        """ Writes all save data to disk, overwriting existing files. May delete files if empty. """
        if len(self.items) == 0:
            delete(self.file_path)
        else:
            dump({
                SAVE_VERSION_KEY: SAVE_VERSION,
                self.ITEMS_KEY: self.items
            }, self.file_path)

    def clear(self) -> None:
        """ Clears all save data. """
        self.items.clear()

    def _add_new_item_from_def(self, def_data: unrealsdk.FStruct, is_weapon: bool) -> None:
        while def_data.UniqueId in self.items:
            def_data.UniqueId = random.randrange(-0x80000000, 0x80000000)

        packed: ItemData = {
            "_description": self._get_description(def_data, is_weapon),
            "_inital": True
        }
        if is_weapon:
            packed.update(pack_weapon_definition_data(def_data))
        else:
            packed.update(pack_item_definition_data(def_data))
        unique_id = cast(int, packed.pop("UniqueId"))

        self.items[unique_id] = packed

    def add_new_item(self, item: unrealsdk.UObject) -> None:
        """
        Adds a new item to the save, rerolling it's unique id if needed.
        """
        self._add_new_item_from_def(item.DefinitionData, item.Class.Name == "WillowWeapon")

    def add_existing_item(self, item: unrealsdk.UObject, existing_save: SaveManager) -> None:
        """
        Adds an item to the save, using existing save data if we've seen it before.

        Intended to be used after loading into a save.
        """
        unique_id = item.DefinitionData.UniqueId
        known_parts = existing_save.items.get(unique_id, None)

        # TODO: this probably doesn't properly handle the case where you pick up a new item with the
        #       same unique id as an existing one - kind of depends on what order this is called in
        if known_parts is None or unique_id in self.items:
            self.add_new_item(item)
        else:
            self.items[unique_id] = known_parts

    def update_item(
        self,
        def_data: unrealsdk.FStruct,
        is_weapon: bool,
        existing_save: SaveManager
    ) -> None:
        """
        Adds an item to the save, and if we've seen it before updates our representation of it to
        use minimal replacements.

        Intended to be used after loading into a save.
        """
        unique_id = def_data.UniqueId
        known_parts = existing_save.items.get(unique_id, None)

        if known_parts is None or unique_id in self.items:
            self._add_new_item_from_def(def_data, is_weapon)
        elif "_inital" not in known_parts:
            self.items[unique_id] = known_parts
        else:
            replacements: ItemData = {
                "_description": known_parts["_description"]
            }

            obj = unrealsdk.GetEngine()  # Just need an arbitrary object

            for field, val in known_parts.items():
                if field[0] == "_":
                    continue
                # We won't be able to find the right version of these parts again, they're
                # dynamically generated
                if isinstance(val, str) and val.startswith("Transient"):
                    continue

                actual_val = getattr(def_data, field)
                if isinstance(actual_val, unrealsdk.UObject):
                    actual_val = obj.PathName(actual_val)

                if actual_val != val:
                    replacements[field] = val

            self.items[unique_id] = replacements

    def fix_definition_data(self, def_data: unrealsdk.FStruct, is_weapon: bool) -> DefDataTuple:
        """
        Looks up an item in the save, and returns what it's definition data tuple should be.
        """
        if def_data.UniqueId not in self.items:
            if is_weapon:
                return expand_weapon_definition_data(def_data)
            else:
                return expand_item_definition_data(def_data)

        if is_weapon:
            parts = pack_weapon_definition_data(def_data)
            parts.update(self.items[def_data.UniqueId])
            return unpack_weapon_definition_data(parts)
        else:
            parts = pack_item_definition_data(def_data)
            parts.update(self.items[def_data.UniqueId])
            return unpack_item_definition_data(parts)

    def remove_item(self, item: unrealsdk.UObject) -> None:
        """
        Removes an item from the save, if we're currently saving it.
        """
        try:
            del self.items[item.DefinitionData.UniqueId]
        except KeyError:
            pass

    @staticmethod
    def _get_description(def_data: unrealsdk.FStruct, is_weapon: bool) -> str:
        description_parts = [f"Level {def_data.ManufacturerGradeIndex}"]

        if is_weapon:
            if def_data.PrefixPartDefinition is not None:
                description_parts.append(def_data.PrefixPartDefinition.PartName)
            if def_data.TitlePartDefinition is not None:
                description_parts.append(def_data.TitlePartDefinition.PartName)
        else:
            if def_data.PrefixItemNamePartDefinition is not None:
                description_parts.append(def_data.PrefixItemNamePartDefinition.PartName)
            if def_data.TitleItemNamePartDefinition is not None:
                description_parts.append(def_data.TitleItemNamePartDefinition.PartName)

        return " ".join(x for x in description_parts if x is not None)
