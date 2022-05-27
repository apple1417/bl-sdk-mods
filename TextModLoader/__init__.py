from __future__ import annotations

import unrealsdk
import os
from enum import Enum, auto
from types import ModuleType
from typing import Any, ClassVar, Dict, Optional

from Mods.ModMenu import Game, ModPriorities, Mods, ModTypes, RegisterMod, SDKMod
from Mods.TextModLoader.constants import (BINARIES_DIR, JSON, META_TAG_AUTHOR, META_TAG_DESCRIPTION,
                                          META_TAG_TITLE, META_TAG_TML_PRIORITY, META_TAG_VERSION,
                                          SETTINGS_IS_MOD_FILE, SETTINGS_META, SETTINGS_MODIFY_TIME,
                                          SETTINGS_RECOMMENDED_GAME, SETTINGS_SPARK_SERVICE_IDX,
                                          TEXT_MOD_PRIORITY, VERSION)
from Mods.TextModLoader.settings import dump_settings, load_auto_enable

CommandExtensions: Optional[ModuleType]
try:
    from Mods import CommandExtensions
except ImportError:
    CommandExtensions = None

__version__: str = ".".join(str(x) for x in VERSION)


def is_hotfix_service(idx: int) -> bool:
    """
    Checks if the given Spark Service index corosponds to the hotfix service.

    Args:
        idx: The Spark Service index to check.
    Returns:
        True if the given service is the hotfix service.
    """
    # Assume this is coming from an offline file which will overwrite it to be valid
    if idx == 0:
        return True

    obj = unrealsdk.FindObject("SparkServiceConfiguration", f"Transient.SparkServiceConfiguration_{idx}")
    if obj is None:
        return False
    return obj.ServiceName.lower() == "micropatch"  # type: ignore


class TextModState(Enum):
    """
    Represent the various states a text mod can be in.

    Transitions
    ===========
    RESTART
      ^ v [Toggle in Mod Menu]
    ENABLED
       ^ [Mod Enable]
    DISABLED   [Other mod with hotfixes enabled]
       +---------> LOCKED_HOTFIXES
       |
       v [Init, if wrong service]
    LOCKED_ONLINE
    """
    ENABLED = auto()
    RESTART = auto()
    DISABLED = auto()
    LOCKED_HOTFIXES = auto()
    LOCKED_ONLINE = auto()


class TextMod(SDKMod):
    Author: str = "Text Mod Loader"
    Version: str = ""

    Types: ModTypes = ModTypes.Gameplay | ModTypes.Utility
    Priority: int = TEXT_MOD_PRIORITY

    any_hotfixes_active: ClassVar[bool] = False
    filename_map: ClassVar[Dict[str, TextMod]] = {}

    is_deleted: bool = False

    state: TextModState = TextModState.DISABLED
    filename: str
    is_in_binaries: bool
    spark_service_idx: Optional[int]
    recommended_game: Optional[Game]

    metadata: JSON

    DESCRIPTIONS_FOR_STATE: ClassVar[Dict[TextModState, str]] = {
        TextModState.RESTART: (
            "This mod was enabled, but will not be re-enabled. Restart the game to remove it fully."
        ),
        TextModState.LOCKED_HOTFIXES: (
            "This mod is <font color=\"#FFFF00\">Locked</font> because you've already run another"
            " mod which uses hotfixes."
        ),
        TextModState.LOCKED_ONLINE: (
            "This mod is <font color=\"#FFFF00\">Locked</font> because it uses a non-existent"
            " hotfix service - are you trying to run an online mod while offline?"
        ),
    }

    STATUSES_FOR_STATE: ClassVar[Dict[TextModState, str]] = {
        TextModState.ENABLED: "Enabled",
        TextModState.RESTART: "<font color=\"#FF6060\">Disabling on Restart</font>",
        TextModState.DISABLED: "Disabled",
        TextModState.LOCKED_HOTFIXES: "<font color=\"#FFFF00\">Locked</font>",
        TextModState.LOCKED_ONLINE: "<font color=\"#FFFF00\">Locked</font>",
    }

    ACTION_DISABLE_RESTART: ClassVar[str] = "Disable"
    ACTION_KEEP_ENABLED: ClassVar[str] = "Keep Enabled"
    ACTION_ENABLE: ClassVar[str] = "Enable"

    SETTINGS_INPUTS_FOR_STATE: ClassVar[Dict[TextModState, Dict[str, str]]] = {
        TextModState.ENABLED: {
            "Enter": ACTION_DISABLE_RESTART,
        },
        TextModState.RESTART: {
            "Enter": ACTION_KEEP_ENABLED,
        },
        TextModState.DISABLED: {
            "Enter": ACTION_ENABLE,
        },
        TextModState.LOCKED_HOTFIXES: {},
        TextModState.LOCKED_ONLINE: {},
    }

    @property  # type: ignore
    def IsEnabled(self) -> bool:
        return self.state in (TextModState.ENABLED, TextModState.RESTART)

    @property
    def auto_enable(self) -> bool:
        return self.state == TextModState.ENABLED

    @property
    def modify_time(self) -> float:
        try:
            return os.path.getmtime(os.path.join(BINARIES_DIR, self.filename))
        except FileNotFoundError:
            self.check_deleted()
            return 0

    @staticmethod
    def register_new(*args: Any, **kwargs: Any) -> TextMod:
        """
        Creates and registers a new text mod object.

        Args:
            *args, **kwargs: Passthroughs to `TextMod` constructor.
        Returns:
            The newly created text mod object.
        """
        mod = TextMod(*args, **kwargs)
        mod.register()
        return mod

    @staticmethod
    def mark_hotfixes_used() -> None:
        """
        Marks that a mod using hotfixes has been executed, and locks all other mods which rely on
         them. This state is irrevesible.
        """
        if not TextMod.any_hotfixes_active:
            TextMod.any_hotfixes_active = True

            for mod in TextMod.filename_map.values():
                if mod.state == TextModState.DISABLED and mod.spark_service_idx is not None:
                    mod.state = TextModState.LOCKED_HOTFIXES
                    mod.update_description()

    def __init__(
        self,
        filename: str,
        spark_service_idx: Optional[int],
        recommended_game: Optional[Game],
        metadata: Optional[JSON] = None
    ) -> None:
        """
        Creates a new Text Mod object.

        Args:
            filename: The filename of the text mod, relative to binaries.
            spark_service_idx: The index of the `SparkServiceConfiguration` objects this mod uses
                                for it's hotfixes, or `None` if it doesn't use hotfixes.
            recommended_game: The game this mod file is for, or `None` if not recognised.
            metadata: Optional. The JSON metadata pulled out of the mod file.
        """
        self.filename = filename
        self.spark_service_idx = spark_service_idx
        self.recommended_game = recommended_game

        if metadata is None:
            metadata = {}
        self.metadata = metadata

        self.Name = metadata.get(META_TAG_TITLE, filename)

        if META_TAG_AUTHOR in metadata:
            self.Author = metadata[META_TAG_AUTHOR]
        if META_TAG_VERSION in metadata:
            self.Version = metadata[META_TAG_VERSION]
        if META_TAG_TML_PRIORITY in metadata:
            self.Priority = metadata[META_TAG_TML_PRIORITY]

        self.is_in_binaries = (
            os.path.dirname(os.path.abspath(os.path.join(BINARIES_DIR, filename))) == BINARIES_DIR
        )

        if spark_service_idx is not None:
            if not is_hotfix_service(spark_service_idx):
                self.state = TextModState.LOCKED_ONLINE
            elif TextMod.any_hotfixes_active:
                self.state = TextModState.LOCKED_HOTFIXES

        self.update_description()

    def Enable(self) -> None:
        if CommandExtensions is not None:
            CommandExtensions.try_handle_command("exec", f"\"{self.filename}\"")
        unrealsdk.GetEngine().GamePlayers[0].Actor.ConsoleCommand(f"exec \"{self.filename}\"")

        self.state = TextModState.ENABLED

        if self.spark_service_idx is not None:
            self.mark_hotfixes_used()

        self.update_description()

    def SettingsInputPressed(self, action: str) -> None:
        if self.state == TextModState.ENABLED and action == TextMod.ACTION_DISABLE_RESTART:
            self.state = TextModState.RESTART
            self.update_auto_enable()
        elif self.state == TextModState.RESTART and action == TextMod.ACTION_KEEP_ENABLED:
            self.state = TextModState.ENABLED
            self.update_auto_enable()
        elif self.state == TextModState.DISABLED and action == TextMod.ACTION_ENABLE:
            self.Enable()
            self.update_auto_enable()
        self.update_description()

    def register(self) -> None:
        """
        Adds this text mod to the mods list and local mod mapping.

        If two mods with the same filename are registered, the older one gets discarded. Since this
         does not preseve state, try to avoid it. :)
        """
        if self.filename in TextMod.filename_map:
            Mods.remove(TextMod.filename_map[self.filename])
        TextMod.filename_map[self.filename] = self
        Mods.append(self)

    def unregister(self) -> None:
        """ Removes this text mod from the mods list and local mod mapping. """
        del TextMod.filename_map[self.filename]
        Mods.remove(self)

    def enable_if_safe(self) -> None:
        """
        Enables the text mod if it's safe (i.e. hotfixes aren't locking it).
        """
        self.SettingsInputPressed(TextMod.ACTION_ENABLE)

    def check_deleted(self) -> None:
        """
        Checks if the mod file's been deleted, and update the description if needed.
        """
        deleted = not os.path.exists(os.path.join(BINARIES_DIR, self.filename))
        if deleted != self.is_deleted:
            self.is_deleted = deleted
            self.update_description()

    def update_description(self) -> None:
        """ Updates the mod's description."""
        self.Description = ""

        if self.recommended_game is not None and self.recommended_game != Game.GetCurrent():
            self.Description += (
                f"<font color=\"#FFFF00\">Warning:</font> This mod is intended for"
                f" {self.recommended_game.name}, and may not function as expected in"
                f" {Game.GetCurrent().name}."
            )

        if self.is_deleted:
            if len(self.Description) > 0:
                self.Description += "\n"
            self.Description += (
                "<font color=\"#FFFF00\">Warning:</font> This mod no longer exists on disk."
            )

        if self.state in TextMod.DESCRIPTIONS_FOR_STATE:
            if len(self.Description) > 0:
                self.Description += "\n\n"
            self.Description += TextMod.DESCRIPTIONS_FOR_STATE[self.state]

        if META_TAG_DESCRIPTION in self.metadata:
            if len(self.Description) > 0:
                self.Description += "\n\n"
            self.Description += self.metadata[META_TAG_DESCRIPTION]

    def serialize_mod_info(self) -> JSON:
        """
        Serializes all cached info about this mod, ready for the settings file.

        Returns:
            The mod info, json formatted.
        """
        game = None if self.recommended_game is None else self.recommended_game.name
        return {
            SETTINGS_IS_MOD_FILE: True,
            SETTINGS_MODIFY_TIME: self.modify_time,
            SETTINGS_SPARK_SERVICE_IDX: self.spark_service_idx,
            SETTINGS_RECOMMENDED_GAME: game,
            SETTINGS_META: self.metadata,
        }

    def update_auto_enable(self) -> None:
        """
        Updates the auto enable state for this mod in the settings file.
        """
        auto_enable_mods = load_auto_enable()
        if self.auto_enable:
            auto_enable_mods.add(self.filename)
        else:
            auto_enable_mods.remove(self.filename)
        dump_settings(auto_enable=auto_enable_mods)


# Because the SDKMod metaclass creates copies of all fields (to make sure you don't affect other
#  mods), we can't overwrite them with properties directly on the class, would make pickling fail
# Instead we have to define them and manually add them here
def TextMod_Status(self: TextMod) -> str:
    return TextMod.STATUSES_FOR_STATE[self.state]


def TextMod_SettingsInputs(self: TextMod) -> Dict[str, str]:
    # Don't let you do anything if the mod file doesn't exist anymore
    if self.is_deleted:
        return {}
    return TextMod.SETTINGS_INPUTS_FOR_STATE[self.state]


TextMod.Status = property(TextMod_Status)  # type: ignore
TextMod.SettingsInputs = property(TextMod_SettingsInputs)  # type: ignore

# This needs to be all the way down here since it relies on `TextMod`
from Mods.TextModLoader.loader import load_all_text_mods  # noqa: E402


def FrontendGFxMovieStart(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
    """
    This function is called upon reaching the main menu, after hotfix objects already exist and all
     the main packages are loaded. We use it to load and enable all mods.
    """
    load_all_text_mods(True)

    unrealsdk.RemoveHook("WillowGame.FrontendGFxMovie.Start", __file__)
    return True


def AddChatMessage(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
    """
    This function is called to post in chat. Normally, it checks if the user the message is from is
     blocked, and then hides it. If it tries this while offline, the game crashes. This is a common
     problem with text mods, so fix it by just removing the check.
    """
    if unrealsdk.GetEngine().SparkInterface.ObjectPointer.IsSparkEnabled():
        return True

    time = caller.GetTimestampString(unrealsdk.FindAll("WillowSaveGameManager")[-1].TimeFormat)
    caller.AddChatMessageInternal(params.PRI.PlayerName + time, params.msg)
    return False


unrealsdk.RunHook("WillowGame.FrontendGFxMovie.Start", __file__, FrontendGFxMovieStart)
unrealsdk.RunHook("WillowGame.TextChatGFxMovie.AddChatMessage", __file__, AddChatMessage)


# Provide an entry in the mods list just so users can see that this is loaded
class TextModLoader(SDKMod):
    Name: str = "Text Mod Loader"
    Author: str = "apple1417"
    Description: str = (
        "Enables loading text mods from the SDK Mods Menu."
    )
    Version: str = __version__

    Types: ModTypes = ModTypes.Library
    Priority: ModPriorities = ModPriorities.Library

    Status: str = "<font color=\"#00FF00\">Loaded</font>"

    ACTION_RELOAD_MODS: ClassVar[str] = "Reload Text Mods"

    SettingsInputs: Dict[str, str] = {
        "R": ACTION_RELOAD_MODS
    }

    def SettingsInputPressed(self, action: str) -> None:
        if action == TextModLoader.ACTION_RELOAD_MODS:
            load_all_text_mods(False)


RegisterMod(TextModLoader())
