import unrealsdk
from typing import Any, ClassVar, Dict, Iterator

from Mods.ModMenu import EnabledSaveType, Mods, ModTypes, Options, RegisterMod, SDKMod

from .RestrictionSets import ALL_RESTRICTION_SETS, BaseRestrictionSet

if __name__ == "__main__":
    import importlib
    import sys
    importlib.reload(sys.modules["Mods.EquipLocker.RestrictionSets"])

    # See https://github.com/bl-sdk/PythonSDK/issues/68
    try:
        raise NotImplementedError
    except NotImplementedError:
        __file__ = sys.exc_info()[-1].tb_frame.f_code.co_filename  # type: ignore


class EquipLocker(SDKMod):
    Name: str = "Equip Locker"
    Author: str = "apple1417"
    Description: str = (
        "Adds various options that prevent you from equipping certain types of items.\n"
        "Useful for allegiance or single rarity or weapon type runs."
    )
    Version: str = "1.3"

    Types: ModTypes = ModTypes.Utility | ModTypes.Gameplay
    SaveEnabledState: EnabledSaveType = EnabledSaveType.LoadWithSettings

    OptionRestrictionMap: Dict[Options.Boolean, BaseRestrictionSet]

    UnableToEquipMessage: ClassVar[str] = f"Locked by {Name}"

    def __init__(self) -> None:
        self.Options = []
        self.OptionRestrictionMap = {}

        for r_set in ALL_RESTRICTION_SETS:
            self.Options.append(Options.Nested(
                r_set.Name,
                r_set.Description,
                r_set.UsedOptions
            ))
            enabled = Options.Boolean(
                "Enable " + r_set.Name,
                "Should this restriction set be enabled.",
                False
            )
            self.OptionRestrictionMap[enabled] = r_set
            self.Options.append(enabled)

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

    def ModOptionChanged(self, option: Options.Base, new_value: Any) -> None:
        pawn = unrealsdk.GetEngine().GamePlayers[0].Actor.Pawn
        if pawn is None:
            return

        for item in self.GetEquippedItems():
            if not item.CanBeUsedBy(pawn):
                pawn.InvManager.InventoryUnreadied(item, True)

    def CanItemBeEquipped(self, item: unrealsdk.UObject) -> bool:
        if item is None:
            return True
        if item.Class.Name == "WillowVehicleWeapon":
            return True

        return not any(
            option.CurrentValue and not r_set.CanItemBeEquipped(item)
            for option, r_set in self.OptionRestrictionMap.items()
        )

    def GetEquippedItems(self) -> Iterator[unrealsdk.UObject]:
        pawn = unrealsdk.GetEngine().GamePlayers[0].Actor.Pawn
        if pawn is None:
            return

        for item in (pawn.InvManager.InventoryChain, pawn.InvManager.ItemChain):
            while item is not None:
                yield item
                item = item.Inventory


instance = EquipLocker()
if __name__ == "__main__":
    unrealsdk.Log(f"[{instance.Name}] Manually loaded")
    for mod in Mods:
        if mod.Name == instance.Name:
            if mod.IsEnabled:
                mod.Disable()
            Mods.remove(mod)
            unrealsdk.Log(f"[{instance.Name}] Removed last instance")

            # Fixes inspect.getfile()
            instance.__class__.__module__ = mod.__class__.__module__
            break
RegisterMod(instance)
