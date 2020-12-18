import unrealsdk
from typing import Dict

from Mods.UserFeedback import ShowHUDMessage

from . import ABCCheat, ABCToggleableCheat, SDKHook


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
            pri = params.WPC.PlayerReplicationInfo
            currency = caller.GetCurrencyTypeInventoryIsSoldIn(params.Item)
            wallet = pri.GetCurrencyOnHand(currency)

            pri.SetCurrencyOnHand(currency, params.ItemPrice)
            unrealsdk.DoInjectedCallNext()
            status = caller.GetItemStatus(params.Item, params.WPC, params.ItemPrice)

            # Revert your money back
            pri.SetCurrencyOnHand(currency, wallet)

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
            pri = caller.PlayerReplicationInfo

            # Save your wallet beforehand
            wallet = pri.GetCurrencyOnHand(currency)

            # Make sure you can afford the item + buy it
            pri.SetCurrencyOnHand(currency, price)
            unrealsdk.DoInjectedCallNext()
            caller.ServerPlayerBoughtItem(
                params.InventoryObject,
                params.Quantity,
                params.bReadyItem,
                params.Shop.ObjectPointer,
                params.bWasItemOfTheDay
            )

            pri.SetCurrencyOnHand(currency, wallet)
            return False

        def PlayerBuyBackInventory(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if caller != unrealsdk.GetEngine().GamePlayers[0].Actor:
                return True
            if not self.IsOn:
                return True

            # Exact same logic as above
            pri = caller.PlayerReplicationInfo
            wallet = pri.GetCurrencyOnHand(params.FormOfCurrency)
            pri.SetCurrencyOnHand(params.FormOfCurrency, params.Price)
            unrealsdk.DoInjectedCallNext()
            caller.PlayerBuyBackInventory(params.FormOfCurrency, params.Price, params.Quantity)
            pri.SetCurrencyOnHand(params.FormOfCurrency, wallet)

            return False

        def ServerPurchaseBlackMarketUpgrade(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if caller != unrealsdk.GetEngine().GamePlayers[0].Actor:
                return True
            if not self.IsOn:
                return True

            # This is a static method so any black market will do
            market = unrealsdk.FindAll("WillowVendingMachineBlackMarket")[-1]
            price = market.StaticGetSellingPriceForBlackMarketInventory(params.BalanceDef, caller)

            # And the same logic once again - this time we know currency is CURRENCY_Eridium, aka 1
            pri = caller.PlayerReplicationInfo
            wallet = pri.GetCurrencyOnHand(1)
            pri.SetCurrencyOnHand(1, price)
            unrealsdk.DoInjectedCallNext()
            caller.ServerPurchaseBlackMarketUpgrade(params.BalanceDef)
            pri.SetCurrencyOnHand(1, wallet)

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
            count += 1  # noqa: SIM113
            obj.ResetInventory()

        ShowHUDMessage(
            self.Name,
            f"Reset {count} shops"
        )
