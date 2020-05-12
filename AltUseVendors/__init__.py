import unrealsdk
from dataclasses import dataclass
from typing import ClassVar, Dict, List
from Mods import AsyncUtil


class AltUseVendors(unrealsdk.BL2MOD):
    Name: ClassVar[str] = "Alt Use Vendors"
    Author: ClassVar[str] = "apple1417"
    Description: ClassVar[str] = (
        "Adds alt use binds to quickly refill health and ammo at their vendors, like in BL3."
    )
    Types: ClassVar[List[unrealsdk.ModTypes]] = [unrealsdk.ModTypes.Utility]
    Version: ClassVar[str] = "1.1"

    UpdatingOption: unrealsdk.Options.Boolean
    Options: List[unrealsdk.Options.Boolean]

    HealthIcon: unrealsdk.UObject
    AmmoIcon: unrealsdk.UObject

    TouchingActors: List[unrealsdk.UObject]

    @dataclass
    class _AmmoInfo:
        ResourceName: str
        AmountPerPurchase: int

    # Going to assume you haven't modded ammo amounts
    # The UCP does edit it to let you refill in one purchage, BUT it also doesn't change the price,
    #  so I think it's more worth sticking with the default amounts
    AmmoMap: ClassVar[Dict[str, _AmmoInfo]] = {
        "AmmoShop_Assault_Rifle_Bullets": _AmmoInfo("Ammo_Combat_Rifle", 54),
        "AmmoShop_Grenade_Protean": _AmmoInfo("Ammo_Grenade_Protean", 3),
        "AmmoShop_Laser_Cells": _AmmoInfo("Ammo_Combat_Laser", 68),
        "AmmoShop_Patrol_SMG_Clip": _AmmoInfo("Ammo_Patrol_SMG", 72),
        "AmmoShop_Repeater_Pistol_Clip": _AmmoInfo("Ammo_Repeater_Pistol", 54),
        "AmmoShop_Rocket_Launcher": _AmmoInfo("Ammo_Rocket_Launcher", 12),
        "AmmoShop_Shotgun_Shells": _AmmoInfo("Ammo_Combat_Shotgun", 24),
        "AmmoShop_Sniper_Rifle_Cartridges": _AmmoInfo("Ammo_Sniper_Rifle", 18)
    }

    UpdateDelay: ClassVar[float] = 0.25

    def __init__(self) -> None:
        # Hopefully I can remove this in a future SDK update
        self.Author += "\nVersion: " + str(self.Version)  # type: ignore

        self.UpdatingOption = unrealsdk.Options.Boolean(
            "Updating Costs",
            "Should the costs of quick buying update live while you're in game. Disabling this"
            " won't show the costs of quick buying anymore, but may help reduce lag.",
            True
        )
        self.Options = [self.UpdatingOption]

        self.HealthIcon = None
        self.AmmoIcon = None

        self.TouchingActors = []

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
                    # TODO: find something that actually plays a sound or something
                    caller.NotifyUserCouldNotAffordAttemptedUse(
                        params.User,
                        params.UsedComponent,
                        params.UsedType
                    )
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

            self.TouchingActors.append(params.Other)
            if self.UpdatingOption.CurrentValue and len(self.TouchingActors) == 1:
                AsyncUtil.RunEvery(self.UpdateDelay, self.OnUpdate, self.Name)

            return True

        def UnTouch(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if str(caller).split(" ")[0] != "WillowVendingMachine":
                return True

            try:
                self.TouchingActors.remove(params.Other)
            except ValueError:  # If the player is not already in the array
                pass

            if self.UpdatingOption.CurrentValue and len(self.TouchingActors) == 0:
                AsyncUtil.CancelFutureCallbacks(self.Name)

            return True

        unrealsdk.RunHook("WillowGame.WillowInteractiveObject.ConditionalReactToUse", self.Name, ConditionalReactToUse)
        unrealsdk.RunHook("WillowGame.WillowInteractiveObject.InitializeFromDefinition", self.Name, InitializeFromDefinition)
        unrealsdk.RunHook("WillowGame.WillowInteractiveObject.Touch", self.Name, Touch)
        unrealsdk.RunHook("WillowGame.WillowInteractiveObject.UnTouch", self.Name, UnTouch)

    def Disable(self) -> None:
        AsyncUtil.CancelFutureCallbacks(self.Name)
        unrealsdk.RemoveHook("WillowGame.WillowInteractiveObject.ConditionalReactToUse", self.Name)
        unrealsdk.RemoveHook("WillowGame.WillowInteractiveObject.InitializeFromDefinition", self.Name)
        unrealsdk.RemoveHook("WillowGame.WillowInteractiveObject.Touch", self.Name)
        unrealsdk.RemoveHook("WillowGame.WillowInteractiveObject.UnTouch", self.Name)

    def CreateIcons(self) -> None:
        if self.HealthIcon is not None and self.AmmoIcon is not None:
            return
        HEALTH_NAME = "Icon_RefillHealth"
        AMMO_NAME = "Icon_RefillAmmo"

        # Incase you're re-execing the file and running a new instance
        self.HealthIcon = unrealsdk.FindObject("InteractionIconDefinition", f"GD_InteractionIcons.Default.{HEALTH_NAME}")
        self.AmmoIcon = unrealsdk.FindObject("InteractionIconDefinition", f"GD_InteractionIcons.Default.{AMMO_NAME}")
        baseIcon = unrealsdk.FindObject("InteractionIconDefinition", "GD_InteractionIcons.Default.Icon_DefaultUse")

        if self.HealthIcon is None:
            self.HealthIcon = unrealsdk.ConstructObject(
                Class=baseIcon.Class,
                Outer=baseIcon.Outer,
                Name=HEALTH_NAME,
                Template=baseIcon
            )
            unrealsdk.KeepAlive(self.HealthIcon)

            self.HealthIcon.Icon = 3
            self.HealthIcon.Action = "UseSecondary"
            self.HealthIcon.Text = "REFILL HEALTH"

        if self.AmmoIcon is None:
            self.AmmoIcon = unrealsdk.ConstructObject(
                Class=baseIcon.Class,
                Outer=baseIcon.Outer,
                Name=AMMO_NAME,
                Template=baseIcon
            )
            unrealsdk.KeepAlive(self.AmmoIcon)

            self.AmmoIcon.Icon = 7
            self.AmmoIcon.Action = "UseSecondary"
            self.AmmoIcon.Text = "REFILL AMMO"

    def OnUpdate(self) -> None:
        # Can't look for pawns directly due to the streaming ones, which will crash the game
        allPawns = [PC.Pawn for PC in unrealsdk.FindAll("WillowPlayerController") if PC.Pawn is not None]

        for vendor in unrealsdk.FindAll("WillowVendingMachine"):
            closetPawn = None
            minDist = -1
            for pawn in allPawns:
                dist = (
                    (vendor.Location.X - pawn.Location.X) ** 2
                    + (vendor.Location.Y - pawn.Location.Y) ** 2  # noqa
                    + (vendor.Location.Z - pawn.Location.Z) ** 2  # noqa
                ) ** 0.5
                if dist < minDist or minDist == -1:
                    dist = minDist
                    closetPawn = pawn

            cost = 0
            if vendor.ShopType == 2:
                cost = self.GetHealthCost(closetPawn, vendor)
            elif vendor.ShopType == 1:
                cost = self.GetAmmoCost(closetPawn, vendor)
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
        fullHealCost = 4 * Vendor.GetSellingPriceForInventory(vial, Pawn.Controller, 1)
        missingHealth = 1 - (Pawn.GetHealth() / Pawn.GetMaxHealth())

        return max(1, int(fullHealCost * missingHealth))

    def BuyHealth(self, Pawn: unrealsdk.UObject, Vendor: unrealsdk.UObject) -> None:
        Pawn.SetHealth(Pawn.GetMaxHealth())

    def GetAmmoCost(self, Pawn: unrealsdk.UObject, Vendor: unrealsdk.UObject) -> int:
        manager = Pawn.Controller.ResourcePoolManager

        ammoNeeded = {}
        for pool in unrealsdk.FindAll("AmmoResourcePool"):
            if pool.Outer != manager:
                continue
            name = pool.Definition.Resource.Name
            ammoNeeded[name] = int(pool.GetMaxValue()) - int(pool.GetCurrentValue())
        # Of course there had to be one odd one out :|
        for pool in unrealsdk.FindAll("ResourcePool"):
            if pool.Outer != manager:
                continue
            if pool.Definition.Resource.Name == "Ammo_Grenade_Protean":
                name = pool.Definition.Resource.Name
                ammoNeeded[name] = int(pool.GetMaxValue()) - int(pool.GetCurrentValue())
                break

        totalPrice = 0
        for item in unrealsdk.FindAll("WillowUsableItem"):
            if item.Owner != Vendor:
                continue
            if item.DefinitionData is None or item.DefinitionData.ItemDefinition is None:
                continue
            name = item.DefinitionData.ItemDefinition.Name
            if name not in self.AmmoMap:
                continue

            amount = self.AmmoMap[name].AmountPerPurchase
            price = Vendor.GetSellingPriceForInventory(item, Pawn.Controller, 1) / amount
            needed = ammoNeeded[self.AmmoMap[name].ResourceName]

            if needed != 0:
                totalPrice += max(1, int(needed * price))

        return totalPrice

    def BuyAmmo(self, Pawn: unrealsdk.UObject, Vendor: unrealsdk.UObject) -> None:
        manager = Pawn.Controller.ResourcePoolManager

        # Don't want to refill nades/rockets in maps that don't sell them
        validPools = []
        for item in unrealsdk.FindAll("WillowUsableItem"):
            if item.Owner != Vendor:
                continue
            if item.DefinitionData is None or item.DefinitionData.ItemDefinition is None:
                continue
            name = item.DefinitionData.ItemDefinition.Name
            if name not in self.AmmoMap:
                continue
            validPools.append(self.AmmoMap[name].ResourceName)

        for pool in unrealsdk.FindAll("AmmoResourcePool"):
            if pool.Outer != manager:
                continue
            if pool.Definition.Resource.Name in validPools:
                pool.SetCurrentValue(pool.GetMaxValue())
        if "Ammo_Grenade_Protean" in validPools:
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
                AsyncUtil.RunEvery(self.UpdateDelay, self.OnUpdate, self.Name)
        # If you turn off updating, stop updating and make sure all vendors are usable at no cost
        else:
            AsyncUtil.CancelFutureCallbacks(self.Name)
            for vendor in unrealsdk.FindAll("WillowVendingMachine"):
                if vendor.ShopType == 1 or vendor.ShopType == 2:
                    vendor.SetUsability(True, 1)
                    vendor.Behavior_ChangeUsabilityCost(1, 0, 0, 1)


instance = AltUseVendors()
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
