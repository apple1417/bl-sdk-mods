import unrealsdk
from dataclasses import dataclass
from typing import ClassVar, Dict, List, Set

from Mods.ModMenu import EnabledSaveType, Mods, ModTypes, Options, RegisterMod, SDKMod

try:
    from Mods import AsyncUtil
except ImportError as ex:
    import webbrowser
    webbrowser.open("https://bl-sdk.github.io/requirements/?mod=Alt%20Use%20Vendors&all")
    raise ex


class AltUseVendors(SDKMod):
    Name: str = "Alt Use Vendors"
    Author: str = "apple1417"
    Description: str = (
        "Adds alt use binds to quickly refill health and ammo at their vendors, like in BL3.\n"
        "\n"
        "If you have issues with stuttering, disable updating costs in settings."
    )
    Version: str = "1.7"

    Types: ModTypes = ModTypes.Utility
    SaveEnabledState: EnabledSaveType = EnabledSaveType.LoadWithSettings

    UpdatingOption: Options.Boolean

    HealthIcon: unrealsdk.UObject
    AmmoIcon: unrealsdk.UObject

    # Dict[<vendor>, Set[<pawn>]]
    TouchingActors: Dict[unrealsdk.UObject, Set[unrealsdk.UObject]]
    # Dict[<vendor>, <cost>]
    VialCosts: Dict[unrealsdk.UObject, int]
    # Dict[<vendor>, Dict[<pool name>, <cost>]]
    AmmoCosts: Dict[unrealsdk.UObject, Dict[str, float]]
    # Dict[<pawn>, Set[<pool>]]
    PlayerAmmoPools: Dict[unrealsdk.UObject, Set[unrealsdk.UObject]]

    @dataclass
    class _AmmoInfo:
        ResourcePoolName: str
        BulletsPerItem: int

    # Going to assume you haven't modded ammo amounts
    # The UCP does edit it to let you refill in one purchage, BUT it also doesn't change the price,
    #  so I think it's more worth sticking with the default amounts
    AMMO_COUNTS: ClassVar[Dict[str, _AmmoInfo]] = {
        "AmmoShop_Assault_Rifle_Bullets": _AmmoInfo("Ammo_Combat_Rifle", 54),
        "AmmoShop_Grenade_Protean": _AmmoInfo("Ammo_Grenade_Protean", 3),
        "AmmoShop_Laser_Cells": _AmmoInfo("Ammo_Combat_Laser", 68),
        "AmmoShop_Patrol_SMG_Clip": _AmmoInfo("Ammo_Patrol_SMG", 72),
        "AmmoShop_Repeater_Pistol_Clip": _AmmoInfo("Ammo_Repeater_Pistol", 54),
        "AmmoShop_Rocket_Launcher": _AmmoInfo("Ammo_Rocket_Launcher", 12),
        "AmmoShop_Shotgun_Shells": _AmmoInfo("Ammo_Combat_Shotgun", 24),
        "AmmoShop_Sniper_Rifle_Cartridges": _AmmoInfo("Ammo_Sniper_Rifle", 18)
    }

    UPDATE_DELAY: ClassVar[float] = 0.25

    HEALTH_ICON_NAME: ClassVar[str] = "Icon_RefillHealth"
    AMMO_ICON_NAME: ClassVar[str] = "Icon_RefillAmmo"

    def __init__(self) -> None:
        self.UpdatingOption = Options.Boolean(
            "Updating Costs",
            "Should the costs of quick buying update live while you're in game. Disabling this"
            " won't show the costs of quick buying anymore, but may help reduce lag.",
            True
        )
        self.Options = [self.UpdatingOption]

        self.HealthIcon = None
        self.AmmoIcon = None

        self.TouchingActors = {}
        self.VialCosts = {}
        self.AmmoCosts = {}
        self.PlayerAmmoPools = {}

    def Enable(self) -> None:
        self.CreateIcons()

        def ConditionalReactToUse(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if caller.Class.Name != "WillowVendingMachine":
                return True
            if params.UsedType != 1:
                return True
            if params.User is None:
                return True

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

            # If you have updating costs on, block payment so we can do it manually
            # This ensures that it always costs the right amount, even if it's displaying wrong
            #  (e.g. if in coop a different player is closer to the vendor)
            if self.UpdatingOption.CurrentValue:
                vendor = caller

                def PayForUsedObject(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
                    if params.UsedObject.ObjectPointer == vendor and params.UsabilityType == 1:
                        unrealsdk.RemoveHook("WillowGame.WillowPlayerController.PayForUsedObject", self.Name)
                        return False
                    else:
                        return True

                unrealsdk.RegisterHook("WillowGame.WillowPlayerController.PayForUsedObject", self.Name, PayForUsedObject)

            PRI.AddCurrencyOnHand(0, -cost)
            PC.SetPendingTransactionStatus(1)

            if caller.ShopType == 2:
                self.BuyHealth(params.User, caller)
            elif caller.ShopType == 1:
                self.BuyAmmo(params.User, caller)

            return True

        def InitializeFromDefinition(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if caller.Class.Name != "WillowVendingMachine":
                return True

            if caller.ShopType == 2:
                params.Definition.HUDIconDefSecondary = self.HealthIcon
                caller.SetUsability(True, 1)
            elif caller.ShopType == 1:
                params.Definition.HUDIconDefSecondary = self.AmmoIcon
                caller.SetUsability(True, 1)

            return True

        # Touch and UnTouch are called whenever a player gets close to an interactive object
        # We use them to disable the update loop when we don't need it, to reduce lag
        # Process it even if updating costs are off so that it switches seamlessly on option change
        def Touch(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if caller.Class.Name != "WillowVendingMachine":
                return True
            if params.Other.Class.Name != "WillowPlayerPawn":
                return True

            # If no one's currently near a vendor, but is about to be, and if updating costs are on,
            #  start the update loop
            if self.UpdatingOption.CurrentValue and len(self.TouchingActors) == 0:
                AsyncUtil.RunEvery(self.UPDATE_DELAY, self.OnUpdate, self.Name)

            if caller not in self.TouchingActors:
                self.TouchingActors[caller] = set()
            self.TouchingActors[caller].add(params.Other)

            return True

        def UnTouch(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if caller.Class.Name != "WillowVendingMachine":
                return True
            if params.Other.Class.Name != "WillowPlayerPawn":
                return True

            try:
                self.TouchingActors[caller].remove(params.Other)
                if len(self.TouchingActors[caller]) == 0:
                    del self.TouchingActors[caller]
            except (KeyError, ValueError):  # If the player or vendor aren't in the dict
                pass

            if self.UpdatingOption.CurrentValue and len(self.TouchingActors) == 0:
                AsyncUtil.CancelFutureCallbacks(self.Name)

            return True

        def WillowShowLoadingMovie(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            # On level change reset all our caching
            self.TouchingActors = {}
            self.VialCosts = {}
            self.AmmoCosts = {}
            self.PlayerAmmoPools = {}
            AsyncUtil.CancelFutureCallbacks(self.Name)
            return True

        def GenerateInventory(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            # Whenever a vendor inventory is generated, update our cached costs
            unrealsdk.DoInjectedCallNext()
            caller.GenerateInventory()

            PC = unrealsdk.GetEngine().GamePlayers[0].Actor

            if caller.ShopType == 1:
                self.AmmoCosts[caller] = {}

            all_items: List[unrealsdk.UObject]
            if unrealsdk.GetVersion() >= (0, 7, 10):
                # This is a static array, which is only got implementedin sdk 0.7.10
                all_items = [
                    item
                    for item in caller.ShopInventory
                    if item is not None
                ]
            else:
                # On older versions we can recover the contents by checking item.Owner, though the
                #  findall makes it much slower
                all_items = [
                    item
                    for item in unrealsdk.FindAll("WillowUsableItem")
                    if item.Owner == caller
                ]

            for item in all_items:
                if item.DefinitionData is None or item.DefinitionData.ItemDefinition is None:
                    continue

                if caller.ShopType == 2:
                    if item.DefinitionData.ItemDefinition.Name == "BuffDrink_HealingInstant":
                        self.VialCosts[caller] = caller.GetSellingPriceForInventory(item, PC, 1)
                        break

                elif caller.ShopType == 1:
                    name = item.DefinitionData.ItemDefinition.Name
                    if name not in self.AMMO_COUNTS:
                        continue

                    info = self.AMMO_COUNTS[name]
                    price = caller.GetSellingPriceForInventory(item, PC, 1) / info.BulletsPerItem
                    self.AmmoCosts[caller][info.ResourcePoolName] = price

            return False

        unrealsdk.RunHook("WillowGame.WillowInteractiveObject.ConditionalReactToUse", self.Name, ConditionalReactToUse)
        unrealsdk.RunHook("WillowGame.WillowInteractiveObject.InitializeFromDefinition", self.Name, InitializeFromDefinition)
        unrealsdk.RunHook("WillowGame.WillowInteractiveObject.Touch", self.Name, Touch)
        unrealsdk.RunHook("WillowGame.WillowInteractiveObject.UnTouch", self.Name, UnTouch)
        unrealsdk.RunHook("WillowGame.WillowPlayerController.WillowShowLoadingMovie", self.Name, WillowShowLoadingMovie)
        unrealsdk.RunHook("WillowGame.WillowVendingMachine.GenerateInventory", self.Name, GenerateInventory)

    def Disable(self) -> None:
        AsyncUtil.CancelFutureCallbacks(self.Name)
        unrealsdk.RemoveHook("WillowGame.WillowInteractiveObject.ConditionalReactToUse", self.Name)
        unrealsdk.RemoveHook("WillowGame.WillowInteractiveObject.InitializeFromDefinition", self.Name)
        unrealsdk.RemoveHook("WillowGame.WillowInteractiveObject.Touch", self.Name)
        unrealsdk.RemoveHook("WillowGame.WillowInteractiveObject.UnTouch", self.Name)
        unrealsdk.RemoveHook("WillowGame.WillowPlayerController.WillowShowLoadingMovie", self.Name)
        unrealsdk.RemoveHook("WillowGame.WillowVendingMachine.GenerateInventory", self.Name)
        unrealsdk.RemoveHook("WillowGame.WillowPlayerController.PayForUsedObject", self.Name)

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
        for vendor, pawns in self.TouchingActors.items():
            # Displayed price is based on closest player
            closet_pawn = None
            min_dist = -1
            for pawn in pawns:
                dist = (
                    (vendor.Location.X - pawn.Location.X) ** 2
                    + (vendor.Location.Y - pawn.Location.Y) ** 2  # noqa
                    + (vendor.Location.Z - pawn.Location.Z) ** 2  # noqa
                ) ** 0.5

                if dist < min_dist or min_dist == -1:
                    dist = min_dist
                    closet_pawn = pawn

            if closet_pawn is None:
                continue

            cost: int
            if vendor.ShopType == 2:
                cost = self.GetHealthCost(closet_pawn, vendor)
            elif vendor.ShopType == 1:
                cost = self.GetAmmoCost(closet_pawn, vendor)
            else:
                continue

            vendor.SetUsability(cost != 0, 1)
            vendor.Behavior_ChangeUsabilityCost(1, 0, cost, 1)

    def GetHealthCost(self, pawn: unrealsdk.UObject, vendor: unrealsdk.UObject) -> int:
        if pawn.GetHealth() == pawn.GetMaxHealth():
            return 0

        # Not sure how this'd happen but just in case
        if vendor not in self.VialCosts:
            return 0

        # Again going to assume you haven't modded how much a vial heals
        full_heal_cost = 4 * self.VialCosts[vendor]
        missing_health = 1 - (pawn.GetHealth() / pawn.GetMaxHealth())

        return max(1, int(full_heal_cost * missing_health))

    def BuyHealth(self, pawn: unrealsdk.UObject, vendor: unrealsdk.UObject) -> None:
        pawn.SetHealth(pawn.GetMaxHealth())

    def LoadPlayerPools(self, pawn: unrealsdk.UObject) -> None:
        if pawn in self.PlayerAmmoPools:
            return

        manager = pawn.Controller.ResourcePoolManager

        if unrealsdk.GetVersion() >= (0, 7, 10):
            # `manager.ResourcePools` is a static array again
            self.PlayerAmmoPools[pawn] = {
                pool
                for pool in manager.ResourcePools
                if (
                    pool is not None
                    and (
                        pool.Class.Name == "AmmoResourcePool"
                        or pool.Definition.Resource.Name == "Ammo_Grenade_Protean"
                    )
                )
            }
        else:
            self.PlayerAmmoPools[pawn] = {
                pool
                for pool in unrealsdk.FindAll("AmmoResourcePool")
                if pool.Outer == manager
            }
            # Of course there had to be one odd one out, leading to yet another findall :|
            for pool in unrealsdk.FindAll("ResourcePool"):
                if pool.Outer != manager:
                    continue
                if pool.Definition.Resource.Name == "Ammo_Grenade_Protean":
                    self.PlayerAmmoPools[pawn].add(pool)
                    break

    def GetAmmoCost(self, pawn: unrealsdk.UObject, vendor: unrealsdk.UObject) -> int:
        self.LoadPlayerPools(pawn)

        if vendor not in self.AmmoCosts:
            return 0
        if pawn not in self.PlayerAmmoPools:
            return 0

        total_cost = 0
        for pool in self.PlayerAmmoPools[pawn]:
            ammo_needed = pool.GetMaxValue() - pool.GetCurrentValue()
            if ammo_needed == 0:
                continue

            name = pool.Definition.Resource.Name
            if name in self.AmmoCosts[vendor]:
                total_cost += max(1, int(ammo_needed * self.AmmoCosts[vendor][name]))

        return total_cost

    def BuyAmmo(self, pawn: unrealsdk.UObject, vendor: unrealsdk.UObject) -> None:
        self.LoadPlayerPools(pawn)

        if vendor not in self.AmmoCosts:
            return
        if pawn not in self.PlayerAmmoPools:
            return

        for pool in self.PlayerAmmoPools[pawn]:
            # Don't want to refill nades/rockets at vendors that don't sell them
            name = pool.Definition.Resource.Name
            if name not in self.AmmoCosts[vendor]:
                continue

            pool.SetCurrentValue(pool.GetMaxValue())

    def ModOptionChanged(self, option: Options.Base, new_value: bool) -> None:
        if option != self.UpdatingOption:
            return

        # If you turn on updating and there are people close to vendors, start updating
        if new_value:
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
