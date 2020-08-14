import unrealsdk
from dataclasses import dataclass
from typing import ClassVar, Dict, List, Set

from Mods.ModMenu import EnabledSaveType, Options, Mods, ModTypes, RegisterMod, SDKMod

try:
    from Mods import AsyncUtil
except ImportError as ex:
    import webbrowser
    webbrowser.open("https://apple1417.github.io/bl2/didntread/?m=Alt%20Use%20Vendors&au")
    raise ex


class AltUseVendors(SDKMod):
    Name: str = "Alt Use Vendors"
    Author: str = "apple1417"
    Description: str = (
        "Adds alt use binds to quickly refill health and ammo at their vendors, like in BL3.\n"
        "\n"
        "If you have issues with stuttering, disable updating costs in settings."
    )
    Version: str = "1.4"

    Types: ModTypes = ModTypes.Utility
    SaveEnabledState: EnabledSaveType = EnabledSaveType.LoadWithSettings

    UpdatingOption: Options.Boolean
    Options: List[Options.Base]

    HealthIcon: unrealsdk.UObject
    AmmoIcon: unrealsdk.UObject

    TouchingActors: Set[unrealsdk.UObject]

    @dataclass
    class _AmmoInfo:
        ResourceName: str
        AmountPerPurchase: int

    # Going to assume you haven't modded ammo amounts
    # The UCP does edit it to let you refill in one purchage, BUT it also doesn't change the price,
    #  so I think it's more worth sticking with the default amounts
    AMMO_MAP: ClassVar[Dict[str, _AmmoInfo]] = {
        "AmmoShop_Assault_Rifle_Bullets": _AmmoInfo("Ammo_Combat_Rifle", 54),
        "AmmoShop_Grenade_Protean": _AmmoInfo("Ammo_Grenade_Protean", 3),
        "AmmoShop_Laser_Cells": _AmmoInfo("Ammo_Combat_Laser", 68),
        "AmmoShop_Patrol_SMG_Clip": _AmmoInfo("Ammo_Patrol_SMG", 72),
        "AmmoShop_Repeater_Pistol_Clip": _AmmoInfo("Ammo_Repeater_Pistol", 54),
        "AmmoShop_Rocket_Launcher": _AmmoInfo("Ammo_Rocket_Launcher", 12),
        "AmmoShop_Shotgun_Shells": _AmmoInfo("Ammo_Combat_Shotgun", 24),
        "AmmoShop_Sniper_Rifle_Cartridges": _AmmoInfo("Ammo_Sniper_Rifle", 18)
    }

    UPDATE_DELAY: ClassVar[float] = 0.5

    HEALTH_ICON_NAME: ClassVar[str] = "Icon_RefillHealth"
    AMMO_ICON_NAME: ClassVar[str] = "Icon_RefillAmmo"

    def __init__(self) -> None:
        self.UpdatingOption = unrealsdk.Options.Boolean(
            "Updating Costs",
            "Should the costs of quick buying update live while you're in game. Disabling this"
            " won't show the costs of quick buying anymore, but may help reduce lag.",
            True
        )
        self.Options = [self.UpdatingOption]

        self.HealthIcon = None
        self.AmmoIcon = None

        self.TouchingActors = set()

    def Enable(self) -> None:
        self.CreateIcons()

        def ConditionalReactToUse(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if params.UsedType != 1:
                return True
            if str(caller).split(" ")[0] != "WillowVendingMachine":
                return True

            # If you have updating costs off we have to take the off money ourselves
            if not self.UpdatingOption.CurrentValue:
                PC = params.User.Controller
                PRI = PC.PlayerReplicationInfo

                wallet = PRI.GetCurrencyOnHand(0)
                cost = 0
                if caller.ShopType == 2:
                    cost = self.GetHealthCost(params.User, caller)
                elif caller.ShopType == 1:
                    cost = self.GetAmmoCost(params.User, caller)
                else:
                    return True

                if cost == 0 or wallet < cost:
                    PC.NotifyUnableToAffordUsableObject(1)
                    return True

                PRI.AddCurrencyOnHand(0, -cost)
                PC.SetPendingTransactionStatus(1)

            if caller.ShopType == 2:
                self.BuyHealth(params.user, caller)
            elif caller.ShopType == 1:
                self.BuyAmmo(params.user, caller)

            return True

        def InitializeFromDefinition(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if str(caller).split(" ")[0] != "WillowVendingMachine":
                return True

            if caller.ShopType == 2:
                params.Definition.HUDIconDefSecondary = self.HealthIcon
                caller.SetUsability(True, 1)
            elif caller.ShopType == 1:
                params.Definition.HUDIconDefSecondary = self.AmmoIcon
                caller.SetUsability(True, 1)

            return True

        def Touch(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if not self.UpdatingOption.CurrentValue:
                return True
            if str(caller).split(" ")[0] != "WillowVendingMachine":
                return True

            self.TouchingActors.add(params.Other)
            if self.UpdatingOption.CurrentValue and len(self.TouchingActors) == 1:
                AsyncUtil.RunEvery(self.UPDATE_DELAY, self.OnUpdate, self.Name)

            return True

        def UnTouch(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if str(caller).split(" ")[0] != "WillowVendingMachine":
                return True

            try:
                self.TouchingActors.remove(params.Other)
            except KeyError:  # If the player is not already in the set
                pass

            if self.UpdatingOption.CurrentValue and len(self.TouchingActors) == 0:
                AsyncUtil.CancelFutureCallbacks(self.Name)

            return True

        def WillowClientDisableLoadingMovie(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            self.TouchingActors.clear()
            return True

        unrealsdk.RunHook("WillowGame.WillowInteractiveObject.ConditionalReactToUse", self.Name, ConditionalReactToUse)
        unrealsdk.RunHook("WillowGame.WillowInteractiveObject.InitializeFromDefinition", self.Name, InitializeFromDefinition)
        unrealsdk.RunHook("WillowGame.WillowInteractiveObject.Touch", self.Name, Touch)
        unrealsdk.RunHook("WillowGame.WillowInteractiveObject.UnTouch", self.Name, UnTouch)
        unrealsdk.RunHook("WillowGame.WillowPlayerController.WillowClientDisableLoadingMovie", self.Name, WillowClientDisableLoadingMovie)

    def Disable(self) -> None:
        AsyncUtil.CancelFutureCallbacks(self.Name)
        unrealsdk.RemoveHook("WillowGame.WillowInteractiveObject.ConditionalReactToUse", self.Name)
        unrealsdk.RemoveHook("WillowGame.WillowInteractiveObject.InitializeFromDefinition", self.Name)
        unrealsdk.RemoveHook("WillowGame.WillowInteractiveObject.Touch", self.Name)
        unrealsdk.RemoveHook("WillowGame.WillowInteractiveObject.UnTouch", self.Name)
        unrealsdk.RemoveHook("WillowGame.WillowPlayerController.WillowClientDisableLoadingMovie", self.Name)

    def CreateIcons(self) -> None:
        if self.HealthIcon is not None and self.AmmoIcon is not None:
            return

        # Incase you're re-execing the file and running a new instance
        self.HealthIcon = unrealsdk.FindObject("InteractionIconDefinition", f"GD_InteractionIcons.Default.{self.HEALTH_ICON_NAME}")
        self.AmmoIcon = unrealsdk.FindObject("InteractionIconDefinition", f"GD_InteractionIcons.Default.{self.AMMO_ICON_NAME}")
        base_icon = unrealsdk.FindObject("InteractionIconDefinition", "GD_InteractionIcons.Default.Icon_DefaultUse")
        PC = unrealsdk.GetEngine().GamePlayers[0].Actor

        if self.HealthIcon is None:
            self.HealthIcon = unrealsdk.ConstructObject(
                Class=base_icon.Class,
                Outer=base_icon.Outer,
                Name=self.HEALTH_ICON_NAME,
                Template=base_icon
            )
            unrealsdk.KeepAlive(self.HealthIcon)

            self.HealthIcon.Icon = 3
            # Setting values directly on the object causes a crash on quitting the game
            # Everything still works fine, not super necessary to fix, but people get paranoid
            # https://github.com/bl-sdk/PythonSDK/issues/45
            PC.ServerRCon(f"set {PC.PathName(self.HealthIcon)} Action UseSecondary")
            PC.ServerRCon(f"set {PC.PathName(self.HealthIcon)} Text REFILL HEALTH")

        if self.AmmoIcon is None:
            self.AmmoIcon = unrealsdk.ConstructObject(
                Class=base_icon.Class,
                Outer=base_icon.Outer,
                Name=self.AMMO_ICON_NAME,
                Template=base_icon
            )
            unrealsdk.KeepAlive(self.AmmoIcon)

            self.AmmoIcon.Icon = 7
            PC.ServerRCon(f"set {PC.PathName(self.AmmoIcon)} Action UseSecondary")
            PC.ServerRCon(f"set {PC.PathName(self.AmmoIcon)} Text REFILL AMMO")

    def OnUpdate(self) -> None:
        # Can't look for pawns directly due to the streaming ones, which will crash the game
        all_pawns = [PC.Pawn for PC in unrealsdk.FindAll("WillowPlayerController") if PC.Pawn is not None]

        for vendor in unrealsdk.FindAll("WillowVendingMachine"):
            closet_pawn = None
            min_dist = -1
            for pawn in all_pawns:
                dist = (
                    (vendor.Location.X - pawn.Location.X) ** 2
                    + (vendor.Location.Y - pawn.Location.Y) ** 2  # noqa
                    + (vendor.Location.Z - pawn.Location.Z) ** 2  # noqa
                ) ** 0.5
                if dist < min_dist or min_dist == -1:
                    dist = min_dist
                    closet_pawn = pawn

            cost: int
            if vendor.ShopType == 2:
                cost = self.GetHealthCost(closet_pawn, vendor)
            elif vendor.ShopType == 1:
                cost = self.GetAmmoCost(closet_pawn, vendor)
            else:
                continue

            vendor.SetUsability(cost != 0, 1)
            vendor.Behavior_ChangeUsabilityCost(1, 0, cost, 1)

    def GetHealthCost(self, Pawn: unrealsdk.UObject, Vendor: unrealsdk.UObject) -> int:
        if Pawn.GetHealth() == Pawn.GetMaxHealth():
            return 0

        vial = None
        for item in unrealsdk.FindAll("WillowUsableItem"):
            if item.Owner != Vendor:
                continue
            if item.DefinitionData is None or item.DefinitionData.ItemDefinition is None:
                continue
            name = item.DefinitionData.ItemDefinition.Name
            if name == "BuffDrink_HealingInstant":
                vial = item
                break
        else:
            return 0

        # Again going to assume you haven't modded how much a vial heals
        full_heal_cost = 4 * Vendor.GetSellingPriceForInventory(vial, Pawn.Controller, 1)
        missing_health = 1 - (Pawn.GetHealth() / Pawn.GetMaxHealth())

        return max(1, int(full_heal_cost * missing_health))

    def BuyHealth(self, Pawn: unrealsdk.UObject, Vendor: unrealsdk.UObject) -> None:
        Pawn.SetHealth(Pawn.GetMaxHealth())

    def GetAmmoCost(self, Pawn: unrealsdk.UObject, Vendor: unrealsdk.UObject) -> int:
        manager = Pawn.Controller.ResourcePoolManager

        ammo_needed = {}
        for pool in unrealsdk.FindAll("AmmoResourcePool"):
            if pool.Outer != manager:
                continue
            name = pool.Definition.Resource.Name
            ammo_needed[name] = int(pool.GetMaxValue()) - int(pool.GetCurrentValue())
        # Of course there had to be one odd one out :|
        for pool in unrealsdk.FindAll("ResourcePool"):
            if pool.Outer != manager:
                continue
            if pool.Definition.Resource.Name == "Ammo_Grenade_Protean":
                name = pool.Definition.Resource.Name
                ammo_needed[name] = int(pool.GetMaxValue()) - int(pool.GetCurrentValue())
                break

        total_price = 0
        for item in unrealsdk.FindAll("WillowUsableItem"):
            if item.Owner != Vendor:
                continue
            if item.DefinitionData is None or item.DefinitionData.ItemDefinition is None:
                continue
            name = item.DefinitionData.ItemDefinition.Name
            if name not in self.AMMO_MAP:
                continue

            amount = self.AMMO_MAP[name].AmountPerPurchase
            price = Vendor.GetSellingPriceForInventory(item, Pawn.Controller, 1) / amount
            needed = ammo_needed[self.AMMO_MAP[name].ResourceName]

            if needed != 0:
                total_price += max(1, int(needed * price))

        return total_price

    def BuyAmmo(self, Pawn: unrealsdk.UObject, Vendor: unrealsdk.UObject) -> None:
        manager = Pawn.Controller.ResourcePoolManager

        # Don't want to refill nades/rockets in maps that don't sell them
        valid_pools = []
        for item in unrealsdk.FindAll("WillowUsableItem"):
            if item.Owner != Vendor:
                continue
            if item.DefinitionData is None or item.DefinitionData.ItemDefinition is None:
                continue
            name = item.DefinitionData.ItemDefinition.Name
            if name not in self.AMMO_MAP:
                continue
            valid_pools.append(self.AMMO_MAP[name].ResourceName)

        for pool in unrealsdk.FindAll("AmmoResourcePool"):
            if pool.Outer != manager:
                continue
            if pool.Definition.Resource.Name in valid_pools:
                pool.SetCurrentValue(pool.GetMaxValue())
        if "Ammo_Grenade_Protean" in valid_pools:
            for pool in unrealsdk.FindAll("ResourcePool"):
                if pool.Outer != manager:
                    continue
                if pool.Definition.Resource.Name == "Ammo_Grenade_Protean":
                    pool.SetCurrentValue(pool.GetMaxValue())
                    break

    def ModOptionChanged(self, Option: unrealsdk.Options.Boolean, newValue: bool) -> None:
        if Option != self.UpdatingOption:
            return

        # If you turn on updating and there are people close to vendors, start updating
        if newValue:
            if len(self.TouchingActors) > 0:
                AsyncUtil.RunEvery(self.UPDATE_DELAY, self.OnUpdate, self.Name)
        # If you turn off updating, stop updating and make sure all vendors are usable at no cost
        else:
            AsyncUtil.CancelFutureCallbacks(self.Name)
            for vendor in unrealsdk.FindAll("WillowVendingMachine"):
                if vendor.ShopType == 1 or vendor.ShopType == 2:
                    vendor.SetUsability(True, 1)
                    vendor.Behavior_ChangeUsabilityCost(1, 0, 0, 1)


instance = AltUseVendors()
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
