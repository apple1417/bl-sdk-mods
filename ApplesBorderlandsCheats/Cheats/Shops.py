import unrealsdk
from typing import Dict

from . import ABCCheat, ABCToggleableCheat, SDKHook
from Mods.UserFeedback import ShowHUDMessage


class FreeShops(ABCToggleableCheat):
    Name = "Free Shops"
    KeybindName = "Toggle Free Shops"

    def GetHooks(self) -> Dict[str, SDKHook]:
        # This function is called to check, among other things, if you can afford the item
        # If free shops are on we want you to always be able to afford it
        def GetItemStatus(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if params.WPC != unrealsdk.GetEngine().GamePlayers[0].Actor:
                return True
            if not self.IsOn:
                return True

            unrealsdk.DoInjectedCallNext()
            status = caller.GetItemStatus(params.Item, params.WPC, params.ItemPrice)

            # If we get back SIS_ItemCanBePurchased (0) we don't have to do anything
            if status == 0:
                return True

            # Otherwise temporarily give all the money you'd need to purcahse it and check again
            PRI = params.WPC.PlayerReplicationInfo
            currency = caller.GetCurrencyTypeInventoryIsSoldIn(params.Item)
            wallet = PRI.GetCurrencyOnHand(currency)

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
            return bool(status != 0)

        # The next three functions are called when you spend money at a shop, so we obviously
        #  have to overwrite them to prevent that
        def ServerPlayerBoughtItem(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if caller != unrealsdk.GetEngine().GamePlayers[0].Actor:
                return True
            if not self.IsOn:
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
            if not self.IsOn:
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
            if not self.IsOn:
                return True

            # This is a static method so any black market will do
            BM = unrealsdk.FindAll("WillowVendingMachineBlackMarket")[-1]
            price = BM.StaticGetSellingPriceForBlackMarketInventory(params.BalanceDef, caller)

            # And the same logic once again - this time we know currency is CURRENCY_Eridium, aka 1
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
