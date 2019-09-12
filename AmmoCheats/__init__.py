import bl2sdk
from os import path
from typing import List
from typing import Dict


class AmmoCheats(bl2sdk.BL2MOD):
    Name: str = "Ammo Cheats"
    Author: str = "apple1417"
    Description: str = (
        "Adds a keybind to cycle infinite ammo modes."
    )
    Types: List[bl2sdk.ModTypes] = [bl2sdk.ModTypes.Utility]
    Version = "1.0"

    KEYBIND_PATH: str = path.join(path.dirname(path.realpath(__file__)), "keybind.txt")

    def __init__(self) -> None:
        # Hopefully I can remove this in a future SDK update
        self.Author += "\nVersion: " + str(self.Version)

    class InfiniteAmmoType:
        OFF = 0
        RELOADS = 1
        FULL = 2

        descriptions = (
            "Off",
            "Free Reloads",
            "Full"
        )
    currentInfiniteAmmoType: int = InfiniteAmmoType.OFF

    def Enable(self) -> None:
        # For weapons
        def ConsumeAmmo(caller: bl2sdk.UObject, function: bl2sdk.UFunction, params: bl2sdk.FStruct) -> bool:
            if self.currentInfiniteAmmoType == self.InfiniteAmmoType.FULL:
                caller.RefillClip()
            return self.currentInfiniteAmmoType == self.InfiniteAmmoType.OFF

        # For grenades
        def ConsumeProjectileResource(caller: bl2sdk.UObject, function: bl2sdk.UFunction, params: bl2sdk.FStruct) -> bool:
            return self.currentInfiniteAmmoType == self.InfiniteAmmoType.OFF

        bl2sdk.RegisterHook("WillowGame.WillowWeapon.ConsumeAmmo", "AmmoCheats", ConsumeAmmo)
        bl2sdk.RegisterHook("WillowGame.WillowPlayerController.ConsumeProjectileResource", "AmmoCheats", ConsumeProjectileResource)

        key = "N"
        try:
            with open(self.KEYBIND_PATH) as f:
                key = f.read()
        except:
            pass

        self.RegisterGameInput("Cycle Infinite Ammo", key)

    def Disable(self) -> None:
        bl2sdk.RemoveHook("WillowGame.WillowWeapon.ConsumeAmmo", "AmmoCheats")
        bl2sdk.RemoveHook("WillowGame.WillowPlayerController.ConsumeProjectileResource", "AmmoCheats")

        self.UnregisterGameInput("Cycle Infinite Ammo")

    def GameInputRebound(self, name: str, key: str) -> None:
        if name == "Cycle Infinite Ammo":
            with open(self.KEYBIND_PATH, "w") as f:
                f.write(key)

    def GameInputPressed(self, input) -> None:  # type: ignore
        if input.Name == "Cycle Infinite Ammo":
            self.currentInfiniteAmmoType = (self.currentInfiniteAmmoType + 1) % 3

            PC = bl2sdk.GetEngine().GamePlayers[0].Actor
            HUDMovie = PC.GetHUDMovie()

            if HUDMovie is None:
                return

            HUDMovie.ClearTrainingText()
            HUDMovie.AddTrainingText(
                "Infinite Ammo: " + self.InfiniteAmmoType.descriptions[self.currentInfiniteAmmoType],
                "Ammo Cheats",
                2,
                (),
                "",
                False,
                0,
                PC.PlayerReplicationInfo,
                True
            )

instance = AmmoCheats()
if __name__ == "__main__":
    bl2sdk.Log("[AC] Manually loaded")
    for mod in bl2sdk.Mods:
        if mod.Name == instance.Name:
            mod.Disable()
            bl2sdk.Mods.remove(mod)
            bl2sdk.Log("[AC] Disabled and removed last instance")
            break
    else:
        bl2sdk.Log("[AC] Could not find previous instance")
    bl2sdk.Log("[AC] Auto-enabling")
    instance.Status = "Enabled"
    instance.SettingsInputs = {"Enter": "Disable"}
    instance.Enable()
bl2sdk.Mods.append(instance)
