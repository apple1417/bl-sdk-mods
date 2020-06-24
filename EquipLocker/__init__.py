import unrealsdk
from typing import Any, ClassVar, List

try:
    from Mods import AAA_OptionsWrapper as OptionsWrapper
except ImportError as ex:
    import webbrowser
    webbrowser.open("https://apple1417.github.io/bl2/didntread/?m=Equip%20Locker&ow")
    raise ex

from Mods.EquipLocker import RestrictionSets

if __name__ == "__main__":
    import importlib
    import sys
    importlib.reload(sys.modules["Mods.AAA_OptionsWrapper"])
    importlib.reload(sys.modules["Mods.EquipLocker.RestrictionSets"])

    # See https://github.com/bl-sdk/PythonSDK/issues/68
    try:
        raise NotImplementedError
    except NotImplementedError:
        __file__ = sys.exc_info()[-1].tb_frame.f_code.co_filename  # type: ignore


class EquipLocker(unrealsdk.BL2MOD):
    Name: ClassVar[str] = "Equip Locker"
    Author: ClassVar[str] = "apple1417"
    Description: ClassVar[str] = (
        "Adds various options that prevent you from equipping certain types of items.\n"
        "Useful for allegiance or single rarity or weapon type runs."
    )
    Types: ClassVar[List[unrealsdk.ModTypes]] = [unrealsdk.ModTypes.Utility]
    Version: ClassVar[str] = "1.0"

    Options: List[OptionsWrapper.Base]

    UnableToEquipMessage: ClassVar[str] = f"Locked by {Name}"

    def __init__(self) -> None:
        self.Author += "\nVersion: " + str(self.Version)  # type: ignore

        self.Options = []
        for rSet in RestrictionSets.ALL_RESTRICTION_SETS:
            self.Options.append(OptionsWrapper.Slider(
                Caption=rSet.Name,
                Description="",
                StartingValue=0,
                MinValue=0,
                MaxValue=0,
                Increment=1
            ))
            self.Options += rSet.Options

    def CanItemBeEquipped(self, item: unrealsdk.UObject) -> bool:
        if item is None:
            return True

        for rSet in RestrictionSets.ALL_RESTRICTION_SETS:
            if not rSet.CanItemBeEquipped(item):
                return False

        return True

    def Enable(self) -> None:
        def GiveTo(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if params.Other != unrealsdk.GetEngine().GamePlayers[0].Actor.Pawn:
                return True

            if not self.CanItemBeEquipped(caller):
                if params.Other.InvManager is None:
                    return True

                params.Other.InvManager.ClientConditionalIncrementPickupStats(caller)
                # Force bReady False so that you don't force equip
                params.Other.InvManager.AddInventory(caller, False, False, params.bPlayPickupSound)
                return False

            return True

        def CanBeUsedBy(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if params.Other != unrealsdk.GetEngine().GamePlayers[0].Actor.Pawn:
                return True
            return self.CanItemBeEquipped(caller)

        def SetItemCardEx(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if params.InventoryItem.ObjectPointer is None:
                return True
            if self.CanItemBeEquipped(params.InventoryItem.ObjectPointer):
                return True

            caller.SetItemCardEx(
                params.WPC,
                params.InventoryItem.ObjectPointer,
                params.CompareAgainstInventoryItem,
                params.CurrencyType,
                params.OverrideValue
            )
            caller.SetLevelRequirement(True, False, False, self.UnableToEquipMessage)

            return False

        def InventoryShouldBeReadiedWhenEquipped(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if caller.Owner != unrealsdk.GetEngine().GamePlayers[0].Actor.Pawn:
                return True
            return self.CanItemBeEquipped(params.WillowInv)

        unrealsdk.RunHook("Engine.Inventory.GiveTo", self.Name, GiveTo)
        unrealsdk.RunHook("Engine.WillowInventory.CanBeUsedBy", self.Name, CanBeUsedBy)
        unrealsdk.RunHook("WillowGame.ItemCardGFxObject.SetItemCardEx", self.Name, SetItemCardEx)
        unrealsdk.RunHook("WillowGame.WillowInventoryManager.InventoryShouldBeReadiedWhenEquipped", self.Name, InventoryShouldBeReadiedWhenEquipped)

    def Disable(self) -> None:
        unrealsdk.RemoveHook("Engine.Inventory.GiveTo", self.Name)
        unrealsdk.RemoveHook("Engine.WillowInventory.CanBeUsedBy", self.Name)
        unrealsdk.RemoveHook("WillowGame.ItemCardGFxObject.SetItemCardEx", self.Name)
        unrealsdk.RemoveHook("WillowGame.WillowInventoryManager.InventoryShouldBeReadiedWhenEquipped", self.Name)

    def ModOptionChanged(self, option: OptionsWrapper.Base, newValue: Any) -> None:
        pawn = unrealsdk.GetEngine().GamePlayers[0].Actor.Pawn
        if pawn is None:
            return
        inv = pawn.InvManager

        for item in (inv.InventoryChain, inv.ItemChain):
            while item is not None:
                next = item.Inventory
                if not item.CanBeUsedBy(pawn):
                    inv.InventoryUnreadied(item, True)
                item = next


instance = EquipLocker()
if __name__ != "__main__":
    unrealsdk.RegisterMod(instance)
else:
    unrealsdk.Log(f"[{instance.Name}] Manually loaded")
    for i in range(len(unrealsdk.Mods)):
        mod = unrealsdk.Mods[i]
        if unrealsdk.Mods[i].Name == instance.Name:
            unrealsdk.Mods[i].Disable()

            unrealsdk.RegisterMod(instance)
            unrealsdk.Mods.remove(instance)
            unrealsdk.Mods[i] = instance
            unrealsdk.Log(f"[{instance.Name}] Disabled and removed last instance")
            break
    else:
        unrealsdk.Log(f"[{instance.Name}] Could not find previous instance")
        unrealsdk.RegisterMod(instance)

    unrealsdk.Log(f"[{instance.Name}] Auto-enabling")
    instance.Status = "Enabled"
    instance.SettingsInputs["Enter"] = "Disable"
    instance.Enable()
