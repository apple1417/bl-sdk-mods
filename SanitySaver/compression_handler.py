import gzip
import json
from pathlib import Path
from typing import Any, IO, Union, cast

_COMPRESS: bool = True


def convert_path(path: Union[str, Path]) -> Path:
    p = Path(path)
    if _COMPRESS:
        if p.suffix == ".gz":
            return p
        else:
            return p.with_suffix(p.suffix + ".gz")
    else:
        if p.suffix == ".gz":
            return p.with_suffix("")
        else:
            return p


def load(path: Union[str, Path]) -> Any:
    """ Loads json data (which may be compressed) from the given file. """
    open_func = gzip.open if _COMPRESS else open

    with open_func(convert_path(path), "rt", encoding="utf8") as file:  # type: ignore
        return json.load(file)


def dump(data: Any, path: Union[str, Path]) -> None:
    """ Dumps the given json data into the given file, compressing it if required. """
    open_func = gzip.open if _COMPRESS else open

    try:
        with open_func(convert_path(path), "wt", encoding="utf8") as file:  # type: ignore
            json.dump(
                data,
                file,
                indent=None if _COMPRESS else 4,
                separators=(",", ":" if _COMPRESS else ": ")
            )
    except PermissionError:
        pass


from .save_manager import _SAVES_DIR  # noqa: E402  # Avoiding circular import


def update_compression(should_compress: bool) -> None:
    """
    Changes if save files will be compressed, and updates any existing files to the correct format.
    """
    global _COMPRESS
    _COMPRESS = should_compress

    for file in _SAVES_DIR.glob("*.json" if should_compress else "*.json.gz"):
        base_file = file.with_suffix("").with_suffix("")

        json_mode, gzip_mode = ("rt", "wt") if should_compress else ("wt", "rt")

        with gzip.open(base_file.with_suffix(".json.gz"), gzip_mode, encoding="utf8") as gzip_file:  # noqa: SIM117
            with open(base_file.with_suffix(".json"), json_mode, encoding="utf8") as json_file:
                file_map = {
                    json_mode: json_file,
                    # This cast shouldn't be needed - `gzip mode` is a literal that's a subset of
                    # the literals typeshed defines as returning IO[str] :/
                    gzip_mode: cast(IO[str], gzip_file)
                }

                # I don't really like repeating all this from above, but we can't use the helpers
                # since files may be in a different state to what we expect them as
                json.dump(
                    json.load(file_map["rt"]),
                    file_map["wt"],
                    indent=None if should_compress else 4,
                    separators=(",", ":" if should_compress else ": ")
                )

        file.unlink()
