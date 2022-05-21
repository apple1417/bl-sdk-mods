from __future__ import annotations

import os
import string
from typing import Iterable, List, Optional

from Mods.ModMenu import Game
from Mods.TextModLoader import TextMod, tml_parser
from Mods.TextModLoader.blimp import parse_blimp_tags
from Mods.TextModLoader.constants import (BINARIES_DIR, BLCMM_GAME_MAP, JSON, META_TAG_AUTHOR,
                                          META_TAG_DESCRIPTION, META_TAG_MAIN_AUTHOR,
                                          META_TAG_TITLE, META_TAG_TML_IGNORE_ME,
                                          META_TAG_TML_PRIORITY, META_TAG_VERSION,
                                          SETTINGS_AUTO_ENABLE, SETTINGS_IS_MOD_FILE, SETTINGS_META,
                                          SETTINGS_MODIFY_TIME, SETTINGS_RECOMMENDED_GAME,
                                          SETTINGS_SPARK_SERVICE_IDX)
from Mods.TextModLoader.settings import dump_settings_file, load_settings_file


def handle_cached_mod_info(filename: str, cached_info: JSON, auto_enable: bool) -> None:
    """
    Looks through a cached file entry, and registers a mod based on it (if applicable).

    May modify the passed in info in-place.

    Args:
        filename: The entry's filename.
        cached_info: The cached info.
        auto_enable: If to enable any mods marked as autoenabled.
    """
    if not cached_info[SETTINGS_IS_MOD_FILE]:
        return
    if META_TAG_TML_IGNORE_ME in cached_info[SETTINGS_META]:
        return

    game_name = cached_info[SETTINGS_RECOMMENDED_GAME]
    mod = TextMod.register_new(
        filename,
        cached_info[SETTINGS_SPARK_SERVICE_IDX],
        None if game_name is None else Game[game_name],
        cached_info[SETTINGS_META]
    )
    if auto_enable and cached_info[SETTINGS_AUTO_ENABLE]:
        mod.enable_if_safe()
        # If we failed to enable, disable auto enable
        if not mod.IsEnabled:
            cached_info[SETTINGS_AUTO_ENABLE] = False


def join_lines_markdown_like(lines: Iterable[str]) -> str:
    """
    Joins a list of lines similarly to how markdown does it, where you need to have an empty line
     in order to add a newline, adjacent lines just get space-seperated.

    Args:
        lines: The list of lines to join.
    Returns:
        The lines joined into a single string.
    """
    def _markdown_iterator() -> Iterable[str]:
        no_space = True
        for line in lines:
            stripped = line.strip()
            if stripped:
                if not no_space:
                    yield " "
                yield stripped
                no_space = False
            else:
                if not no_space:
                    yield "\n"
                no_space = True
    return "".join(_markdown_iterator())


def join_sentence(entries: List[str], final_connector: str = "and") -> str:
    """
    Joins a list of strings as in a sentence listing them.
    Args:
        lines: The list of entries to join.
        final_connector: The word to use to connect the final two entries.
    Returns:
        The list joined into a single string.
    """
    def _sentence_iterator() -> Iterable[str]:
        for entry in entries[:-1]:
            yield entry
            yield ", "
        if len(entries) > 2:
            yield final_connector
            yield " "
        yield entries[-1]
    return "".join(_sentence_iterator())


def find_edge_characters(lines: List[str]) -> str:
    """
    Given a list of strings, try detect characters used to create ASCII art edges around them.

    Will always return whitespace, so that you can pass the return directly to `str.strip()`.

    Args:
        lines: The list of lines to search though.
    Returns:
        A string containing all detected characters.
    """
    strip_chars = string.whitespace

    # Do one quick pass removing existing whitespace
    stripped_lines = list(filter(None, (line.strip() for line in lines)))
    if not stripped_lines:
        return strip_chars

    edges = (
        stripped_lines[0],
        stripped_lines[-1],
        "".join(line[0] for line in stripped_lines),
        "".join(line[-1] for line in stripped_lines),
    )

    for edge in edges:
        threshold = 0.8 * len(edge)
        symbols = list(filter(lambda c: not c.isalnum(), edge))
        if len(symbols) > threshold:
            strip_chars += "".join(set(symbols))

    return strip_chars


def parse_metadata(comments: Iterable[str]) -> JSON:
    """
    Parses out the metadata tags stored in a comment block.
    Will try extract a default description even if no `@description` tags are found.

    Args:
        comments: A list of extracted comments.
        no_untagged: If to disable extracting data from untagged comment contents.
    Returns:
        A dict mapping each found metadata tag to it's value.
    """
    found_tags, untagged_lines = parse_blimp_tags(comments)

    metadata: JSON = {}
    if META_TAG_TITLE in found_tags:
        metadata[META_TAG_TITLE] = found_tags[META_TAG_TITLE][0].strip()
    if META_TAG_VERSION in found_tags:
        metadata[META_TAG_VERSION] = found_tags[META_TAG_VERSION][0].strip()

    authors = []
    if META_TAG_MAIN_AUTHOR in found_tags:
        authors.append(found_tags[META_TAG_MAIN_AUTHOR][0])
    if META_TAG_AUTHOR in found_tags:
        for author in found_tags[META_TAG_AUTHOR]:
            authors.append(author.strip())
    if authors:
        metadata[META_TAG_AUTHOR] = join_sentence(authors)

    if META_TAG_DESCRIPTION in found_tags:
        metadata[META_TAG_DESCRIPTION] = join_lines_markdown_like(found_tags[META_TAG_DESCRIPTION])
    else:
        strip_chars = find_edge_characters(untagged_lines)
        metadata[META_TAG_DESCRIPTION] = join_lines_markdown_like(
            line.strip(strip_chars) for line in untagged_lines
        )

    if META_TAG_TML_PRIORITY in found_tags:
        try:
            metadata[META_TAG_TML_PRIORITY] = int(found_tags[META_TAG_TML_PRIORITY][0])
        except ValueError:
            pass

    if META_TAG_TML_IGNORE_ME in found_tags:
        metadata[META_TAG_TML_IGNORE_ME] = True

    return metadata


def parse_and_register_mod_file(file_path: str) -> JSON:
    """
    Parses through a given file, creating and registering a mod out of it if possible.

    Args:
        file_path: The full path to the mod file.
    Returns:
        The info to cache for this file.
    """
    spark_service_idx: Optional[int]
    game_str: Optional[str]
    comments: List[str]

    try:
        spark_service_idx, game_str, comments = tml_parser.parse(file_path)
    except (tml_parser.BLCMMParserError, ValueError, RuntimeError):
        return {
            SETTINGS_IS_MOD_FILE: False,
            SETTINGS_MODIFY_TIME: os.path.getmtime(file_path),
        }

    game = None if game_str is None else BLCMM_GAME_MAP.get(game_str, None)
    mod = TextMod(
        os.path.basename(file_path),
        spark_service_idx,
        game,
        parse_metadata(comments)
    )

    if META_TAG_TML_IGNORE_ME not in mod.metadata:
        mod.register()

    return mod.serialize_mod_info()


def load_all_text_mods(auto_enable: bool) -> None:
    """
    (Re-)Loads all text mods from binaries.

    Args:
        auto_enable: If to enable any mods marked as such in the settings file.
    """
    # Clear disabled and locked text mods - anything else has special state we want to keep
    for mod in list(TextMod.filename_map.values()):
        # Completely ignore custom registered files from outside of binaries
        if not mod.is_in_binaries:
            continue
        # Check for deletion on enabled files, but still keep them in the list
        if mod.IsEnabled:
            mod.check_deleted()
            continue
        mod.unregister()

    # Cache mod info cause looking through the files each time is slow
    mod_info: JSON = load_settings_file()
    new_mod_info: JSON = {}

    for filename in os.listdir(BINARIES_DIR):
        file_path = os.path.join(BINARIES_DIR, filename)
        if os.path.isdir(file_path):
            continue

        # Don't reload active mods
        if filename in TextMod.filename_map:
            continue

        modify_time = os.path.getmtime(file_path)

        # If the file hasn't been modified since we last saw it, load cached values
        if filename in mod_info and modify_time <= mod_info[filename][SETTINGS_MODIFY_TIME]:
            try:
                handle_cached_mod_info(filename, mod_info[filename], auto_enable)
                new_mod_info[filename] = mod_info[filename]
                continue
            # If something's formatted wrong, read from the file again and recreate it
            except KeyError:
                pass

        new_mod_info[filename] = parse_and_register_mod_file(file_path)

    dump_settings_file(new_mod_info)
