import unrealsdk
from abc import ABCMeta, abstractmethod
from typing import Callable, ClassVar, Dict, List, Tuple
from Mods.UserFeedback import ShowHUDMessage

SDKHook = Callable[[unrealsdk.UObject, unrealsdk.UFunction, unrealsdk.FStruct], bool]


# Base class for our cheats
class ABCCheat(metaclass=ABCMeta):
    Name: ClassVar[str]
    KeybindName: ClassVar[str]

    # Callback for when the cheat's keybind is pressed
    @abstractmethod
    def OnPress(self) -> None:
        raise NotImplementedError

    # Returns a dict of the hooks the cheat needs, bound to that particular cheat - i.e. the hooks'
    #  behavior should only change if you modify the attributes on the cheat you created it on
    def GetHooks(self) -> Dict[str, SDKHook]:
        return {}


# Base class for cheats with multiple options that the keybind should cycle through
# Expects you to add a bunch of static strings for each option, and put them all in 'Order'
# Behaves somewhat like an enum
class ABCCycleableCheat(ABCCheat):
    Order: ClassVar[Tuple[str, ...]]

    def __init__(self, value: str = "") -> None:
        if value == "":
            value = self.Order[0]
        if value not in self.Order:
            raise ValueError
        self.value = value

    def __eq__(self, obj: object) -> bool:
        if isinstance(obj, str):
            return self.value == obj
        elif isinstance(obj, type(self)):
            return self.value == obj.value
        return False

    def OnPress(self) -> None:
        self.value = self.Order[(self.Order.index(self.value) + 1) % len(self.Order)]
        ShowHUDMessage(self.Name, f"{self.Name}: {self.value}")
        self.OnCycle()

    def OnCycle(self) -> None:
        pass


# Base class for cheats that the keybind should just toggle on or off
class ABCToggleableCheat(ABCCycleableCheat):
    OFF: ClassVar[str] = "Off"
    ON: ClassVar[str] = "On"
    Order = (OFF, ON)


# The list of all our cheats
# Using a class so we can reference the inner cycleable cheat's values for comparisons
class ABCList:
    class InfiniteAmmo(ABCCycleableCheat):
        Name = "Infinite Ammo"
        KeybindName = "Cycle Infinite Ammo"

        OFF: ClassVar[str] = "Off"
        RELOADS: ClassVar[str] = "Free Reloads"
        FULL: ClassVar[str] = "Full"
        Order = (OFF, RELOADS, FULL)

        def GetHooks(self) -> Dict[str, SDKHook]:
            # For weapons
            def ConsumeAmmo(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
                PC = unrealsdk.GetEngine().GamePlayers[0].Actor
                if PC is None or PC.Pawn is None or caller != PC.Pawn.Weapon:
                    return True
                if self == self.FULL:
                    caller.RefillClip()
                return self == self.OFF

            # For grenades
            def ConsumeProjectileResource(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
                if caller != unrealsdk.GetEngine().GamePlayers[0].Actor:
                    return True
                return self == ABCList.InfiniteAmmo.OFF

            return {
                "WillowGame.WillowWeapon.ConsumeAmmo": ConsumeAmmo,
                "WillowGame.WillowPlayerController.ConsumeProjectileResource": ConsumeProjectileResource,
            }

    class GodMode(ABCCycleableCheat):
        Name = "God Mode"
        KeybindName = "Cycle God Mode"

        OFF: ClassVar[str] = "Off"
        ALLOWDAMAGE: ClassVar[str] = "1 HP"
        FULL: ClassVar[str] = "Full"
        Order = (OFF, ALLOWDAMAGE, FULL)

        def GetHooks(self) -> Dict[str, SDKHook]:
            # Blocking this function stops knockback for full god mode
            def TakeDamage(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
                if caller != unrealsdk.GetEngine().GamePlayers[0].Actor.Pawn:
                    return True

                return self != self.FULL

            def SetHealth(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
                if caller != unrealsdk.GetEngine().GamePlayers[0].Actor.Pawn:
                    return True

                if self == self.FULL:
                    # The previous function should prevent getting here, but just in case
                    return False
                elif self == self.ALLOWDAMAGE:
                    if params.NewHealth < 1:
                        unrealsdk.DoInjectedCallNext()
                        caller.SetHealth(1)
                        return False

                return True

            return {
                "WillowGame.WillowPlayerPawn.TakeDamage": TakeDamage,
                "Engine.Pawn.SetHealth": SetHealth
            }

    class OneShot(ABCToggleableCheat):
        Name = "One Shot Mode"
        KeybindName = "Toggle One Shot Mode"

        def GetHooks(self) -> Dict[str, SDKHook]:
            def TakeDamage(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
                PC = unrealsdk.GetEngine().GamePlayers[0].Actor

                if params.InstigatedBy != PC:
                    return True

                if self != self.ON:
                    return True

                game = unrealsdk.FindAll("WillowCoopGameInfo")[-1]
                if game.IsFriendlyFire(caller, params.InstigatedBy.Pawn):
                    return True

                caller.SetShieldStrength(0)
                # Try set the health to 1 so that your shot kills them, giving xp
                # Only do it if they have more than 1 health though, so that you don't get stuck in a
                #  loop if you somehow deal less than 1 damage
                if caller.GetHealth() > 1:
                    caller.SetHealth(1)
                else:
                    caller.SetHealth(0)

                return True

            return {"Engine.Pawn.TakeDamage": TakeDamage}

    class InstantCooldown(ABCToggleableCheat):
        Name = "Instant Cooldown"
        KeybindName = "Toggle Instant Cooldown"

        def GetHooks(self) -> Dict[str, SDKHook]:
            # We can use the same simple function for both action and melee skills
            def StartActiveMeleeSkillCooldown(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
                if caller != unrealsdk.GetEngine().GamePlayers[0].Actor:
                    return True
                return self == self.OFF

            return {
                "WillowGame.WillowPlayerController.StartActiveSkillCooldown": StartActiveMeleeSkillCooldown,
                "WillowGame.WillowPlayerController.StartMeleeSkillCooldown": StartActiveMeleeSkillCooldown,
            }

    class PassiveMode(ABCCycleableCheat):
        Name = "Passive Enemies"
        KeybindName = "Cycle Passive Enemies"

        # These are in the same order as in the games's struct
        OFF: ClassVar[str] = "Off"  # Technically this is OPINION_Enemy
        NEUTRAL: ClassVar[str] = "Neutral"
        FRIENDLY: ClassVar[str] = "Friendly"
        Order = (OFF, NEUTRAL, FRIENDLY)

        def OnCycle(self) -> None:
            allegiance = unrealsdk.FindObject("PawnAllegiance", "GD_AI_Allegiance.Allegiance_Player")
            allegiance2 = unrealsdk.FindObject("PawnAllegiance", "GD_AI_Allegiance.Allegiance_Player_NoLevel")

            allegiance.bForceAllOtherOpinions = self != self.OFF
            allegiance2.bForceAllOtherOpinions = self != self.OFF

            allegiance.ForcedOtherOpinion = self.Order.index(self.value)
            allegiance2.ForcedOtherOpinion = self.Order.index(self.value)

    class FreeShops(ABCToggleableCheat):
        Name = "Free Shops"
        KeybindName = "Toggle Free Shops"

        def GetHooks(self) -> Dict[str, SDKHook]:
            # This function is called to check, among other things, if you can afford the item
            # If free shops are on we want you to always be able to afford it
            def GetItemStatus(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
                if params.WPC != unrealsdk.GetEngine().GamePlayers[0].Actor:
                    return True
                if self == self.OFF:
                    return True

                unrealsdk.DoInjectedCallNext()
                status: int = caller.GetItemStatus(params.Item, params.WPC, params.ItemPrice)

                # If we get back SIS_ItemCanBePurchased (0) we don't have to do anything
                if status == 0:
                    return True

                # Otherwise temporarily give all the money you'd need to purcahse it and check again
                PRI: unrealsdk.UObject = params.WPC.PlayerReplicationInfo
                currency: int = caller.GetCurrencyTypeInventoryIsSoldIn(params.Item)
                wallet: int = PRI.GetCurrencyOnHand(currency)

                PRI.SetCurrencyOnHand(currency, params.ItemPrice)
                unrealsdk.DoInjectedCallNext()
                status = caller.GetItemStatus(params.Item, params.WPC, params.ItemPrice)

                # Revert your money back
                PRI.SetCurrencyOnHand(currency, wallet)

                # If the status now is SIS_ItemCanBePurchased (0) then we were just missing money, and
                #  we want the actual status to be ignore that
                # We can't directly change the return value of the function, only if it executes
                # However, if the function doesn't execute then it's return value is None
                # As luck would have it this ends up casting to 0 - the exact value we want to set
                return status != 0

            # The next three functions are called when you spend money at a shop, so we obviously
            #  have to overwrite them to prevent that
            def ServerPlayerBoughtItem(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
                if caller != unrealsdk.GetEngine().GamePlayers[0].Actor:
                    return True
                if self == self.OFF:
                    return True

                # Copy a bit of logic to get the right shop
                shop = params.Shop
                if shop is None:
                    shop = caller.ActiveShop
                    # If it's still none then just let the game deal with it
                    if shop is None:
                        return True
                else:
                    # This is an FScriptInterface, need to get the object
                    shop = shop.ObjectPointer

                currency = shop.GetCurrencyTypeInventoryIsSoldIn(params.InventoryObject)
                price = shop.GetSellingPriceForInventory(
                    params.InventoryObject,
                    caller,
                    params.Quantity
                )
                PRI = caller.PlayerReplicationInfo

                # Save your wallet beforehand
                wallet = PRI.GetCurrencyOnHand(currency)

                # Make sure you can afford the item + buy it
                PRI.SetCurrencyOnHand(currency, price)
                unrealsdk.DoInjectedCallNext()
                caller.ServerPlayerBoughtItem(
                    params.InventoryObject,
                    params.Quantity,
                    params.bReadyItem,
                    params.Shop.ObjectPointer,
                    params.bWasItemOfTheDay
                )

                PRI.SetCurrencyOnHand(currency, wallet)
                return False

            def PlayerBuyBackInventory(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
                if caller != unrealsdk.GetEngine().GamePlayers[0].Actor:
                    return True
                if self == self.OFF:
                    return True

                # Exact same logic as above
                PRI = caller.PlayerReplicationInfo
                wallet = PRI.GetCurrencyOnHand(params.FormOfCurrency)
                PRI.SetCurrencyOnHand(params.FormOfCurrency, params.Price)
                unrealsdk.DoInjectedCallNext()
                caller.PlayerBuyBackInventory(params.FormOfCurrency, params.Price, params.Quantity)
                PRI.SetCurrencyOnHand(params.FormOfCurrency, wallet)

                return False

            def ServerPurchaseBlackMarketUpgrade(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
                if caller != unrealsdk.GetEngine().GamePlayers[0].Actor:
                    return True
                if self == self.OFF:
                    return True

                # This is a static method so any black market will do
                BM = unrealsdk.FindAll("WillowVendingMachineBlackMarket")[0]
                price = BM.StaticGetSellingPriceForBlackMarketInventory(params.BalanceDef, caller)

                # And the same logic once again
                PRI = caller.PlayerReplicationInfo
                wallet = PRI.GetCurrencyOnHand(1)
                PRI.SetCurrencyOnHand(1, price)
                unrealsdk.DoInjectedCallNext()
                caller.ServerPurchaseBlackMarketUpgrade(params.BalanceDef)
                PRI.SetCurrencyOnHand(1, wallet)

                return False

            return {
                "WillowGame.WillowVendingMachineBase.GetItemStatus": GetItemStatus,
                "WillowGame.WillowPlayerController.ServerPlayerBoughtItem": ServerPlayerBoughtItem,
                "WillowGame.WillowPlayerController.PlayerBuyBackInventory": PlayerBuyBackInventory,
                "WillowGame.WillowPlayerController.ServerPurchaseBlackMarketUpgrade": ServerPurchaseBlackMarketUpgrade,
            }

    class Ghost(ABCToggleableCheat):
        Name = "Ghost Mode"
        KeybindName = "Ghost Mode"

        MinSpeed: ClassVar[int] = 100
        DefaultSpeed: ClassVar[int] = 2500
        MaxSpeed: ClassVar[int] = 100000
        SpeedIncrement: ClassVar[float] = 1.2

        Pawn: unrealsdk.UObject
        LastLevel: str
        LastOff: bool

        def __init__(self) -> None:
            super().__init__()
            self.LastLevel = ""
            self.LastOff = True

        def OnCycle(self) -> None:
            # If you switch levels while in ghost it gets turned off automatically, so don't do
            #  anything if you toggle it off after changing map
            engine = unrealsdk.GetEngine()
            level = engine.GetCurrentWorldInfo().GetStreamingPersistentMapName()
            if level != self.LastLevel and self == self.OFF:
                self.LastLevel = level
                return
            self.LastLevel = level

            # If you somehow triggered this on the menu don't do anything
            if level == "menumap":
                return

            PC = engine.GamePlayers[0].Actor
            if self == self.ON:
                # We need to save the pawn so that we can possess the right one again later
                self.Pawn = PC.Pawn

                PC.ServerSpectate()
                PC.bCollideWorld = False
                PC.SpectatorCameraSpeed = self.DefaultSpeed

                self.LastOff = False
            else:
                # So that turning this off with a preset doesn't re-tp you
                if not self.LastOff:
                    self.Pawn.Location = (PC.Location.X, PC.Location.Y, PC.Location.Z)
                    PC.Possess(self.Pawn, True)

                    self.LastOff = True

        def GetHooks(self) -> Dict[str, SDKHook]:
            # Let scrolling adjust your movement speed
            def InputKey(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
                if params.Event != 0:
                    return True
                PC = unrealsdk.GetEngine().GamePlayers[0].Actor
                speed = PC.SpectatorCameraSpeed
                if params.key == "MouseScrollUp":
                    PC.SpectatorCameraSpeed = min(speed * self.SpeedIncrement, self.MaxSpeed)
                elif params.key == "MouseScrollDown":
                    PC.SpectatorCameraSpeed = max(speed / self.SpeedIncrement, self.MinSpeed)
                return True
            return {"WillowGame.WillowUIInteraction.InputKey": InputKey}

    class KillAll(ABCCheat):
        Name = "Kill All"
        KeybindName = "Kill All"

        def OnPress(self) -> None:
            playerPools = []
            # Unintuitively, `unrealsdk.GetEngine().GamePlayers` does not hold remote players
            for pawn in unrealsdk.FindAll("WillowPlayerPawn"):
                if pawn.HealthPool.Data is not None:
                    playerPools.append(pawn.HealthPool.Data)
            for pool in unrealsdk.FindAll("HealthResourcePool"):
                if pool in playerPools:
                    continue
                pool.CurrentValue = 0

    class LevelUp(ABCCheat):
        Name = "Level Up"
        KeybindName = "Level Up"

        def OnPress(self) -> None:
            unrealsdk.GetEngine().GamePlayers[0].Actor.ExpLevelUp(True)

    class OPLevel(ABCCheat):
        Name = "Add OP Level"
        KeybindName = "Add OP Level"

        def OnPress(self) -> None:
            PC = unrealsdk.GetEngine().GamePlayers[0].Actor
            rep = PC.PlayerReplicationInfo
            if rep.NumOverpowerLevelsUnlocked == PC.GetMaximumPossibleOverpowerModifier():
                ShowHUDMessage(
                    self.Name,
                    "You are already at the maximum OP level"
                )
            else:
                rep.NumOverpowerLevelsUnlocked += 1
                ShowHUDMessage(
                    self.Name,
                    f"You have now unlocked OP {rep.NumOverpowerLevelsUnlocked}"
                )

    class Suicide(ABCCheat):
        Name = "Suicide"
        KeybindName = "Suicide"

        def OnPress(self) -> None:
            unrealsdk.GetEngine().GamePlayers[0].Actor.CausePlayerDeath(True)

    class TPFastTravel(ABCCheat):
        Name = "Teleport Between Fast Travel Stations"
        KeybindName = "Teleport Between Fast Travel Stations"

        TPClass: ClassVar[str] = "FastTravelStation"

        def __init__(self) -> None:
            self.LastTravelIndex: int = 0
            self.AllTravels: List[str] = [""]

        def OnPress(self) -> None:
            # Get the list of all station names in the world
            currentTravels = []
            for obj in unrealsdk.FindAll(self.TPClass):
                if obj.TravelDefinition is None:
                    continue
                currentTravels.append(obj.TravelDefinition.Name)

            # If the current station is not in the list then we must have changed worlds
            if self.AllTravels[self.LastTravelIndex] not in currentTravels:
                # Set to -1 so that it advances to the first one
                self.LastTravelIndex = -1
                self.AllTravels = currentTravels

            if len(self.AllTravels) == 0:
                return

            self.LastTravelIndex = (self.LastTravelIndex + 1) % len(self.AllTravels)
            station = self.AllTravels[self.LastTravelIndex]
            unrealsdk.GetEngine().GamePlayers[0].Actor.TeleportPlayerToStation(station)

    class TPLevelTravel(TPFastTravel):
        Name = "Teleport Between Level Transitions"
        KeybindName = "Teleport Between Level Transitions"

        TPClass = "LevelTravelStation"

    class ResetShops(ABCCheat):
        Name = "Reset Shops"
        KeybindName = "Reset Shops"

        def OnPress(self) -> None:
            count = 0
            for obj in unrealsdk.FindAll("WillowVendingMachine"):
                if obj.Name == "Default__WillowVendingMachine":
                    continue
                count += 1
                obj.ResetInventory()

            ShowHUDMessage(
                self.Name,
                f"Reset {count} shops"
            )

    class ReviveSelf(ABCCheat):
        Name = "Revive Self"
        KeybindName = "Revive Self"

        def OnPress(self) -> None:
            Pawn = unrealsdk.GetEngine().GamePlayers[0].Actor.Pawn
            if Pawn.bIsInjured and not Pawn.bIsDead:
                Pawn.GoFromInjuredToHealthy()
                Pawn.ClientOnRevived()


# Holds information about the current cheat state, generated automatically from 'ABCList'
# Also keeps track of all the hooks its cheats need - generated automatically again
class ABCOptions:
    All: Tuple[ABCCheat, ...]
    Hooks: Dict[str, List[SDKHook]]

    def __init__(self) -> None:
        allCheats: List[ABCCheat] = []

        for val in ABCList.__dict__.values():
            # If the value is not a cheat class
            if not isinstance(val, type) or not issubclass(val, ABCCheat):
                continue
            allCheats.append(val())

        self.All = tuple(allCheats)

        # Put hook collisions into a list so that they can both run
        # Double hooking a function can be finicky so we're assuming the hooks are written so that
        #  the order they're run in doesn't matter
        # If really needed you can hook a sub/super class instead
        self.Hooks = {}
        for cheat in self.All:
            for hook, function in cheat.GetHooks().items():
                if hook in self.Hooks:
                    self.Hooks[hook].append(function)
                else:
                    self.Hooks[hook] = [function]
