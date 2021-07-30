import gzip
import json
from pathlib import Path
from typing import Any, IO, Union, cast

from .helpers import log_traceback

_COMPRESS: bool = True


def _convert_path(path: Union[str, Path], compress: bool) -> Path:
    p = Path(path)
    if compress:
        if p.suffix == ".gz":
            return p
        else:
            return p.with_suffix(p.suffix + ".gz")
    else:
        if p.suffix == ".gz":
            return p.with_suffix("")
        else:
            return p


def _delete_single_file(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass
    except OSError:
        log_traceback()


def _dump_file(data: Any, file: IO[str], compress: bool) -> None:
    json.dump(
        data,
        file,
        indent=None if _COMPRESS else 4,
        separators=(",", ":" if _COMPRESS else ": ")
    )


def _update_single_file_compression(path: Path, compress: bool) -> None:
    try:
        json_mode, gzip_mode = ("rt", "wt") if compress else ("wt", "rt")

        with gzip.open(_convert_path(path, True), gzip_mode, encoding="utf8") as gzip_file:  # noqa: SIM117
            with open(_convert_path(path, False), json_mode, encoding="utf8") as json_file:
                file_map = {
                    json_mode: json_file,
                    # This cast shouldn't be needed - `gzip mode` is a literal that's a subset
                    # of the literals typeshed defines as returning IO[str] :/
                    gzip_mode: cast(IO[str], gzip_file)
                }

                data = json.load(file_map["rt"])
                _dump_file(data, file_map["wt"], compress)

        path.unlink()
    # In this version of python, gzip throws base `OSError`s, which also catches file not founds
    except OSError:
        log_traceback()


def load(path: Union[str, Path]) -> Any:
    """ Loads json data (which may be compressed) from the given file. """
    correct_file = _convert_path(path, _COMPRESS)
    incorrect_file = _convert_path(path, not _COMPRESS)

    # If the wrong file is newer than the correct once, convert it and use it instead
    if incorrect_file.exists():
        if (
            not correct_file.exists()
            or incorrect_file.stat().st_mtime > correct_file.stat().st_mtime
        ):
            _update_single_file_compression(correct_file, _COMPRESS)
        else:
            _delete_single_file(incorrect_file)

    open_func = gzip.open if _COMPRESS else open

    with open_func(correct_file, "rt", encoding="utf8") as file:  # type: ignore
        return json.load(file)


def dump(data: Any, path: Union[str, Path]) -> None:
    """ Dumps the given json data into the given file, compressing it if required. """
    open_func = gzip.open if _COMPRESS else open

    try:
        with open_func(_convert_path(path, _COMPRESS), "wt", encoding="utf8") as file:  # type: ignore
            _dump_file(data, file, _COMPRESS)
    except OSError:
        log_traceback()

    _delete_single_file(_convert_path(path, not _COMPRESS))


def delete(path: Union[str, Path]) -> None:
    """ Deletes the given file, including a version with incorrect compression (if it exists). """
    _delete_single_file(_convert_path(path, True))
    _delete_single_file(_convert_path(path, False))


from .save_manager import _SAVES_DIR  # noqa: E402  # Avoiding circular import


def update_compression(compress: bool) -> None:
    """
    Changes if save files will be compressed, and updates any existing files to the correct format.
    """
    global _COMPRESS
    _COMPRESS = compress

    for file in _SAVES_DIR.glob("*.json" if compress else "*.json.gz"):
        _update_single_file_compression(file, compress)
