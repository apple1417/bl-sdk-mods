# ruff: noqa: D103

if True:
    assert __import__("mods_base").__version_info__ >= (1, 5), "Please update the SDK"

from typing import Any

from unrealsdk.hooks import Block

from mods_base import build_mod, hook

__version__: str
__version_info__: tuple[int, ...]


@hook("WillowGame.FrontendGFxMovie:ShowMOTD")
@hook("WillowGame.WillowPlayerController:CanAcessOakUpsell")
def blocker(*_: Any) -> type[Block]:
    return Block

mod = build_mod(hooks=[blocker])
