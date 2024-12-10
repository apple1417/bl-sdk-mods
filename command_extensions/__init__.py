# ruff: noqa: D103

if True:
    assert __import__("mods_base").__version_info__ >= (1, 5), "Please update the SDK"

from mods_base import build_mod

__version__: str
__version_info__: tuple[int, ...]


mod = build_mod()
