import bl2sdk
import json
import os
from abc import ABCMeta
from abc import abstractmethod
from typing import Callable
from typing import Dict
from typing import List
from typing import Tuple

if __name__ == "__main__":
    # __file__ isn't set when you call this through a pyexec, so we have to do something real silly
    # If we cause an exception then the traceback will contain the file name, which we can regex out
    import re, traceback
    try:
        fake += 1
    except NameError as e:
        match = re.search(r"File \"(.*?)\", line", traceback.format_exc())
        if match is None:
            __file__ = "C\:"
            bl2sdk.Log(f"[ABC] File path: {__file__}")
        else:
            __file__ = match.group(1)
            bl2sdk.Log(f"[ABC] File path: {__file__}")


# Small helper classes I have to define out here to be able to inherit from
class ABCCheat(metaclass=ABCMeta):
    KeybindName: str

    @abstractmethod
    def Callback(self) -> None:
        raise NotImplementedError

class ABCCycleableCheat(ABCCheat):
    Name: str
    Order: Tuple[str, ...]

    def __init__(self, value: str = "") -> None:
        if value == "":
            value = self.Order[0]
        if value not in self.Order:
            raise ValueError
        self.value = value

    def __eq__(self, obj: object) -> bool:
        if isinstance(obj, str):
            return self.value == obj
        elif type(self) == type(obj):
            return self.value == obj.value  # type: ignore
        return False

    def Callback(self) -> None:
        self.value = self.Order[(self.Order.index(self.value) + 1) % len(self.Order)]

        PC = bl2sdk.GetEngine().GamePlayers[0].Actor
        HUDMovie = PC.GetHUDMovie()

        if HUDMovie is None:
            return

        HUDMovie.ClearTrainingText()
        HUDMovie.AddTrainingText(
            f"{self.Name}: {self.value}",
            self.Name,
            2,
            (),
            "",
            False,
            0,
            PC.PlayerReplicationInfo,
            True
        )

class ApplesBorderlandsCheats(bl2sdk.BL2MOD):
    Name: str = "Apple's Borderlands Cheats"
    Author: str = "apple1417"
    Description: str = (
        "Adds keybinds performing various cheaty things"
    )
    Types: List[bl2sdk.ModTypes] = [bl2sdk.ModTypes.Utility]
    Version = "1.0"
    SettingsInputs = {
        "Enter": "Enable",
        "R": "Reset Keybinds"
    }

    KEYBIND_PATH: str = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Keybinds.json")

    # Holds information about the current cheat state, as well as defines each cheat
    class Cheats:
        class InfiniteAmmo(ABCCycleableCheat):
            Name = " Infinite Ammo"
            KeybindName = "Cycle Infinite Ammo"

            OFF: str = "Off"
            RELOADS: str = "Free Reloads"
            FULL: str = "Full"
            Order = (OFF, RELOADS, FULL)

        class GodMode(ABCCycleableCheat):
            Name = "God Mode"
            KeybindName = "Cycle God Mode"

            OFF: str = "Off"
            ALLOWDAMAGE: str = "Prevent Death"
            FULL: str = "No Damage"
            Order = (OFF, ALLOWDAMAGE, FULL)

        class OneShot(ABCCycleableCheat):
            Name = "One Shot Mode"
            KeybindName = "Toggle One Shot Mode"

            OFF: str = "Off"
            ON: str = "On"
            Order = (OFF, ON)

        class PassiveMode(ABCCycleableCheat):
            Name = "Passive Mode"
            KeybindName = "Cycle Passive Mode"

            # These are in the same order as in the games's struct
            OFF: str = "Off"  # Technically this is OPINION_Enemy
            NEUTRAL: str = "Neutral"
            FRIENDLY: str = "Friendly"
            Order = (OFF, NEUTRAL, FRIENDLY)

            def Callback(self) -> None:
                super().Callback()

                allegiance = bl2sdk.FindObject("PawnAllegiance", "GD_AI_Allegiance.Allegiance_Player")
                allegiance2 = bl2sdk.FindObject("PawnAllegiance", "GD_AI_Allegiance.Allegiance_Player_NoLevel")

                allegiance.bForceAllOtherOpinions = self != self.OFF
                allegiance2.bForceAllOtherOpinions = self != self.OFF

                allegiance.ForcedOtherOpinion = self.Order.index(self.value)
                allegiance2.ForcedOtherOpinion = self.Order.index(self.value)

        class KillAll(ABCCheat):
            KeybindName = "Kill All"

            def Callback(self) -> None:
                playerPool = bl2sdk.GetEngine().GamePlayers[0].Actor.Pawn.HealthPool.Data
                for pool in bl2sdk.FindAll("HealthResourcePool"):
                    if pool == playerPool:
                        continue
                    pool.CurrentValue = 0

        class LevelUp(ABCCheat):
            KeybindName = "Level Up"

            def Callback(self) -> None:
                bl2sdk.GetEngine().GamePlayers[0].Actor.ExpLevelUp(True)

        """
        This would be neat but it's a bit too crashy for my tastes

        class RaiseGearLevel(ABCCheat):
            Name = "Raise Equipped Gear Level"
            KeybindName = "Raise Equipped Gear Level"

            # This is it's own function so that we can overwrite it to slightly adjust the cheat
            def adjustItem(self, item: bl2sdk.UObject) -> None:
                item.DefinitionData.GameStage += 1
                item.DefinitionData.ManufacturerGradeIndex += 1

            def Callback(self) -> None:
                inv = bl2sdk.GetEngine().GamePlayers[0].Actor.Pawn.InvManager

                weapon = inv.InventoryChain
                while weapon != None:
                    self.adjustItem(weapon)

                    ammo = weapon.ReloadCnt
                    # This function will add extra ammo for having picked up a new weapon
                    # We don't want it to do so, so we have to save the count before hand then
                    #  remove the extra after
                    weapon.InitializeInternal()

                    weapon.ReloadCnt = ammo
                    weapon.AmmoPool.Data.AddCurrentValueImpulse(
                        -weapon.DefinitionData.WeaponTypeDefinition.StartingAmmoCount
                    )

                    weapon = weapon.Inventory

                item = inv.ItemChain
                while item != None:
                    self.adjustItem(item)
                    item.InitializeInternal()
                    item = item.Inventory
        """


        def __init__(self) -> None:
            self.ammo: ABCCycleableCheat = self.InfiniteAmmo()
            self.god: ABCCycleableCheat = self.GodMode()
            self.one: ABCCycleableCheat = self.OneShot()
            self.passive: ABCCycleableCheat = self.PassiveMode()

            self.all: Tuple[ABCCheat, ...] = (
                self.ammo,
                self.god,
                self.one,
                self.passive,
                self.KillAll(),
                self.LevelUp()
            )

    def __init__(self) -> None:
        # Hopefully I can remove this in a future SDK update
        self.Author += "\nVersion: " + str(self.Version)

        self.options = self.Cheats()

    def SettingsInputPressed(self, name: str) -> None:
        if name == "Enable":
            self.Status = "Enabled"
            self.SettingsInputs["Enter"] = "Disable"
            self.Enable()
        elif name == "Disable":
            self.Status = "Disabled"
            self.SettingsInputs["Enter"] = "Enable"
        elif name == "Reset Keybinds":
            if self.Status == "Enabled":
                for name in self.Keybinds:
                    self.UnregisterGameInput(name)
                    self.RegisterGameInput(name, "None")
                    self.Keybinds[name] = "None"
            try:
                os.remove(self.KEYBIND_PATH)
            except FileNotFoundError:
                pass

    def Enable(self) -> None:
        # For weapon infinite ammo
        def ConsumeAmmo(caller: bl2sdk.UObject, function: bl2sdk.UFunction, params: bl2sdk.FStruct) -> bool:
            if self.options.ammo == self.Cheats.InfiniteAmmo.FULL:
                caller.RefillClip()
            return self.options.ammo == self.Cheats.InfiniteAmmo.OFF

        # For grenade infinite ammo
        def ConsumeProjectileResource(caller: bl2sdk.UObject, function: bl2sdk.UFunction, params: bl2sdk.FStruct) -> bool:
            return self.options.ammo == self.Cheats.InfiniteAmmo.OFF

        # For full god and one shot mode
        def TakeDamage(caller: bl2sdk.UObject, function: bl2sdk.UFunction, params: bl2sdk.FStruct) -> bool:
            PC = bl2sdk.GetEngine().GamePlayers[0].Actor
            if caller == PC.Pawn:
                return self.options.god != self.Cheats.GodMode.FULL

            if params.InstigatedBy != PC:
                return True

            if self.options.one == self.Cheats.OneShot.ON:
                # Set the health low so that your shot kills it, rather than just to 0 killing it
                #  straight away
                bl2sdk.DoInjectedCallNext()
                caller.SetHealth(0.01)

            return True

        # For 1hp god mode
        def SetHealth(caller: bl2sdk.UObject, function: bl2sdk.UFunction, params: bl2sdk.FStruct) -> bool:
            if caller != bl2sdk.GetEngine().GamePlayers[0].Actor.Pawn:
                return True

            # This function is never called if you have full god mode on, so this is safe
            if params.NewHealth > caller.GetHealth() or params.NewHealth > 1:
                return True

            if self.options.god != self.Cheats.GodMode.ALLOWDAMAGE:
                return True

            bl2sdk.DoInjectedCallNext()
            caller.SetHealth(1)
            return False

        bl2sdk.RegisterHook("WillowGame.WillowWeapon.ConsumeAmmo", "ApplesBorderlandsCheats", ConsumeAmmo)
        bl2sdk.RegisterHook("WillowGame.WillowPlayerController.ConsumeProjectileResource", "ApplesBorderlandsCheats", ConsumeProjectileResource)
        bl2sdk.RegisterHook("Engine.Pawn.TakeDamage", "ApplesBorderlandsCheats", TakeDamage)
        bl2sdk.RegisterHook("Engine.Pawn.SetHealth", "ApplesBorderlandsCheats", SetHealth)

        loadedBinds: Dict[str, str] = {}
        try:
            with open(self.KEYBIND_PATH) as file:
                loadedBinds = json.load(file)
        except FileNotFoundError:
            pass

        # Limit to just the binds associated with the cheats, incase someone messes with the file
        self.Keybinds: Dict[str, str] = {}
        for cheat in self.options.all:
            if cheat.KeybindName in loadedBinds:
                self.Keybinds[cheat.KeybindName] = loadedBinds[cheat.KeybindName]
            else:
                # By default we don't want these bound
                self.Keybinds[cheat.KeybindName] = "None"

        with open(self.KEYBIND_PATH, "w") as file:
            json.dump(self.Keybinds, file, indent=2)

        for name in self.Keybinds:
            self.RegisterGameInput(name, self.Keybinds[name])

    def Disable(self) -> None:
        bl2sdk.RemoveHook("WillowGame.WillowWeapon.ConsumeAmmo", "ApplesBorderlandsCheats")
        bl2sdk.RemoveHook("WillowGame.WillowPlayerController.ConsumeProjectileResource", "ApplesBorderlandsCheats")
        bl2sdk.RemoveHook("Engine.Pawn.TakeDamage", "ApplesBorderlandsCheats")
        bl2sdk.RemoveHook("Engine.Pawn.SetHealth", "ApplesBorderlandsCheats")

        for name in self.Keybinds:
            self.UnregisterGameInput(name)

    def GameInputRebound(self, name: str, key: str) -> None:
        if name not in self.Keybinds:
            return

        self.Keybinds[name] = key

        with open(self.KEYBIND_PATH, "w") as file:
            json.dump(self.Keybinds, file, indent=2)

    def GameInputPressed(self, input) -> None:  # type: ignore
        for cheat in self.options.all:
            if input.Name == cheat.KeybindName:
                cheat.Callback()

instance = ApplesBorderlandsCheats()
if __name__ == "__main__":
    bl2sdk.Log("[ABC] Manually loaded")
    for mod in bl2sdk.Mods:
        if mod.Name == instance.Name:
            mod.Disable()
            bl2sdk.Mods.remove(mod)
            bl2sdk.Log("[ABC] Disabled and removed last instance")
            break
    else:
        bl2sdk.Log("[ABC] Could not find previous instance")

    bl2sdk.Log("[ABC] Auto-enabling")
    instance.Status = "Enabled"
    instance.SettingsInputs["Enter"] = "Disable"
    instance.Enable()
bl2sdk.Mods.append(instance)
