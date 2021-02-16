import unrealsdk
from typing import Callable, Dict

from .helpers import (DefDataTuple, expand_item_definition_data, expand_weapon_definition_data,
                      get_all_items_and_weapons)
from .save_manager import STASH_NAME, SaveManager

SDKHook = Callable[[unrealsdk.UObject, unrealsdk.UFunction, unrealsdk.FStruct], bool]
AllHooks: Dict[str, SDKHook] = {}


def hook(hook: str) -> Callable[[SDKHook], SDKHook]:
    def decorator(_func: SDKHook) -> SDKHook:
        AllHooks[hook] = _func
        return _func
    return decorator


def Block(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
    """ Just a small helper for a few places we need to unconditionally block a function call. """
    return False


"""
So at it's most basic, to remove sanity check all we really want to do is force
`WPC.ValidateWeaponDefinition` and `WPC.ValidateItemDefinition` to always return True.

Unfortuantly, the sdk doesn't support custom returns, so instead we redefine every function that
calls one of those two as if it always returned True.
"""


@hook("WillowGame.WillowPlayerController.ApplyDLCInventorySaveGameData")
def ApplyDLCInventorySaveGameData(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
    """ It doesn't seem like this is actually called anywhere, but better safe than sorry. """

    if not caller.IsLocalPlayerController():
        caller.ServerItemSaveGameDataCompleted()
        return False

    inv_manager = caller.GetPawnInventoryManager()

    for idx, saved_item in enumerate(params.ItemData):
        if saved_item.bEquipped:
            ServerSetItemSaveGameData(
                caller,
                idx,
                saved_item.DefinitionData,
                saved_item.Quantity,
                saved_item.bEquipped,
                saved_item.Mark
            )
            continue
        inv_manager.ClientAddItemToBackpack(
            expand_item_definition_data(saved_item.DefinitionData),
            saved_item.Quantity,
            saved_item.Mark,
            False,
            14
        )

    for idx, saved_weap in enumerate(params.WeaponData):
        if saved_weap.QuickSlot != 0:
            ServerSetWeaponSaveGameData(
                caller,
                idx,
                saved_weap.DefinitionData,
                saved_weap.QuickSlot,
                saved_weap.Mark
            )
            continue
        inv_manager.ClientAddWeaponToBackpack(
            expand_weapon_definition_data(saved_weap.DefinitionData),
            saved_weap.Mark,
            False,
            14
        )

    inv_manager.UpdateBackpackInventoryCount()
    caller.ServerItemSaveGameDataCompleted()

    return False


@hook("WillowGame.WillowPlayerController.ApplyItemSaveGameData")
def ApplyItemSaveGameData(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
    inv_manager = caller.GetPawnInventoryManager()
    is_local = caller.IsLocalPlayerController()

    for idx, saved_item in enumerate(params.SaveGame.ItemData):
        if saved_item.bEquipped:
            if caller.Role == 3:  # ROLE_Authority
                ServerSetItemSaveGameData(
                    caller,
                    idx,
                    saved_item.DefinitionData,
                    saved_item.Quantity,
                    saved_item.bEquipped,
                    saved_item.Mark
                )
            continue
        if is_local:
            inv_manager.ClientAddItemToBackpack(
                expand_item_definition_data(saved_item.DefinitionData),
                saved_item.Quantity,
                saved_item.Mark,
                False,
                14
            )

    if is_local:
        caller.UnloadableDlcItemData = list(params.SaveGame.UnloadableDlcItemData)
    caller.ServerItemSaveGameDataCompleted()

    return False


@hook("WillowGame.WillowPlayerController.ApplyWeaponSaveGameData")
def ApplyWeaponSaveGameData(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
    """
    We need to call `FixupSavedWeapons` at the start here, but it uses an out argument.
    If we block `ValidateWeaponDefinition` and `IsLocalPlayerController`, so they return false, this
    function will do nothing except make that call for us
    """
    unrealsdk.RunHook("WillowGame.WillowPlayerController.IsLocalPlayerController", __name__, Block)
    unrealsdk.RunHook("WillowGame.WillowPlayerController.ValidateWeaponDefinition", __name__, Block)

    caller.ApplyWeaponSaveGameData(params.SaveGame)

    unrealsdk.RemoveHook("WillowGame.WillowPlayerController.IsLocalPlayerController", __name__)
    unrealsdk.RemoveHook("WillowGame.WillowPlayerController.ValidateWeaponDefinition", __name__)

    # Now we can recreate the call like normal
    inv_manager = caller.GetPawnInventoryManager()
    is_local = caller.IsLocalPlayerController()

    for idx, saved_weap in enumerate(params.SaveGame.WeaponData):
        if saved_weap.QuickSlot != 0:
            if caller.Role == 3:  # ROLE_Authority
                ServerSetWeaponSaveGameData(
                    caller,
                    idx,
                    saved_weap.WeaponDefinitionData,
                    saved_weap.QuickSlot,
                    saved_weap.Mark
                )
            continue
        if is_local:
            inv_manager.ClientAddWeaponToBackpack(
                expand_weapon_definition_data(saved_weap.WeaponDefinitionData),
                saved_weap.Mark,
                False,
                14
            )

    if is_local:
        caller.UnloadableDlcWeaponData = list(params.SaveGame.UnloadableDlcWeaponData)
    caller.ServerItemSaveGameDataCompleted()

    return False


"""
The next two functions we hook are ones we also need to call as part of the three above.
If you just call them directly the sdk ignores the hook though, so we define them in two parts, one
normal function and one hook function.

Fwiw it doesn't seem like these functions are actually called anywhere outside of the three above,
but better to be safe (just like the dlc one).
"""


@hook("WillowGame.WillowPlayerController.ServerSetItemSaveGameData")
def ServerSetItemSaveGameData_Hook(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
    ServerSetItemSaveGameData(caller, params.Index, params.DefinitionData, params.Quantity, params.bEquipped, params.Mark)
    return False


@hook("WillowGame.WillowPlayerController.ServerSetWeaponSaveGameData")
def ServerSetWeaponSaveGameData_Hook(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
    ServerSetWeaponSaveGameData(caller, params.Index, params.DefinitionData, params.QuickSlot, params.Mark)
    return False


def ServerSetItemSaveGameData(caller: unrealsdk.UObject, idx: int, def_data: unrealsdk.UObject, quantity: int, equipped: bool, mark: int) -> None:
    item = caller.Spawn(def_data.ItemDefinition.InventoryClass)

    if item is None:
        return

    inv_pawn = caller.GetInventoryPawn()

    item.ItemLocation = 14
    item.InitializeFromDefinitionData(
        expand_item_definition_data(def_data),
        inv_pawn,
        False
    )
    item.Quantity = quantity
    item.SetMark(mark)
    item.GiveTo(inv_pawn, equipped)


def ServerSetWeaponSaveGameData(caller: unrealsdk.UObject, idx: int, def_data: unrealsdk.UObject, slot: int, mark: int) -> None:
    weap = caller.Spawn(def_data.WeaponTypeDefinition.InventoryClass)

    if weap is None:
        return

    inv_pawn = caller.GetInventoryPawn()

    weap.ItemLocation = 14
    weap.InitializeFromDefinitionData(
        expand_weapon_definition_data(def_data),
        inv_pawn,
        False
    )
    weap.SetMark(mark)
    weap.StoredAmmo = 0
    inv_pawn.InvManager.PendingQuickSlot = slot
    weap.GiveTo(inv_pawn, slot != 0)


"""
We also want to save items that don't serialize, and we want the game to save these items as best it
can, so that you can still somewhat use them without the mod.

This doesn't require overwriting any behaviour, so we can just hook the outermost functions.
"""


@hook("WillowGame.WillowPlayerController.GeneratePlayerSaveGame")
def GeneratePlayerSaveGame(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
    # This hook is also called when you load into any map, after the load hook
    # It doesn't break anything so might as well let it
    new_save = SaveManager(caller.SaveGameName)
    existing_save = SaveManager(caller.SaveGameName)
    existing_save.load()

    for item in get_all_items_and_weapons(caller.GetPawnInventoryManager()):
        if item.Class.Name == "WillowWeapon" and not item.CanBeSaved():
            continue
        new_save.add_item(item.DefinitionData, item.Class.Name == "WillowWeapon", existing_save)

    new_save.write()

    return True


# We can't hook LoadPlayerSaveGame itself because the item objects don't exist yet
@hook("WillowGame.WillowPlayerController.ApplyPlayerSaveGameData")
def ApplyPlayerSaveGameData(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
    # Exit early for new characters, this'll fire again anyway on sq
    save_name = caller.GetSaveGameNameFromid(params.SaveGame.SaveGameId)
    if save_name is None:
        return True

    save_manager = SaveManager(save_name)
    save_manager.load()

    for item in params.SaveGame.ItemData:
        if item is None or item.DefinitionData is None:
            continue
        item.DefinitionData = save_manager.apply_replacements(item.DefinitionData, False)

    for weap in params.SaveGame.WeaponData:
        if weap is None or weap.WeaponDefinitionData is None:
            continue
        weap.WeaponDefinitionData = save_manager.apply_replacements(weap.WeaponDefinitionData, True)

    save_manager.write()

    return True


"""
One complication to our custom save system is that in some situations some parts get unloaded
*before* the game saves gear.

This is indistingishable from there not being a part in that slot, so as a workaround we force load
parts as the items are created. This will not get the game to save these for us though, we still
need to do that outselves.
"""


@hook("WillowGame.WillowItem.OnCreate")
@hook("WillowGame.WillowWeapon.OnCreate")
def OnCreate(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
    all_parts: DefDataTuple
    if caller.Class.Name == "WillowWeapon":
        all_parts = expand_weapon_definition_data(caller.DefinitionData)
    else:
        all_parts = expand_item_definition_data(caller.DefinitionData)
    for part in all_parts:
        if not isinstance(part, unrealsdk.UObject):
            continue
        unrealsdk.KeepAlive(part)
    return True


"""
Deal with the bank/stash.

The items in these only actually exist while the container is open, meaning this has to be done a
little differently. Opening them also runs the validate calls again, we need to remove those too.
"""


@hook("WillowGame.WillowInventoryStorage.Open")
def Open(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
    if caller.ChestIsOpen:
        return False
    # We'll set this later cause we re-call this function and don't want it to early exit

    PC = caller.Outer.GetOwningPlayerController()
    if PC is None:
        return False
    inv_manager = PC.GetPawnInventoryManager()

    save_manager: SaveManager
    if caller == inv_manager.TheBank:
        save_manager = SaveManager(PC.SaveGameName, True)
    elif caller == inv_manager.TheStash:
        save_manager = SaveManager(STASH_NAME)
    elif caller in (inv_manager.TheGrinder, inv_manager.TheMailBox):
        return True
    else:
        unrealsdk.Log("[SanitySaver] Could not identify opened container!")
        return True
    save_manager.load()

    PC.OnChestOpened(caller)

    """
    This is a bit of a mess.

    All items are stored as serial number structs, which contain a static array. This means we can't
    ever pass one of these structs, or even whole the list, from Python back into UnrealScript.

    So how do we convert these to a useable format?
    `WillowInventory.CreateInventoryFromSerialNumber`

    We still can't call this ourself though, we have to get something else to. And unfortuantly it
    happens to only be called by the very function we have to overwrite to remove the sanity check
    in the first place.

    The only way we can actually extract item references is by hooking the sanity check functions.
    Hooking them means we have to force all items to get sanity checked and be destroyed, but
    luckily there's handy functions to recreate them  from the definition with our changes.
    """

    inv_list = []

    def ValidateItemWeaponDefinition(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
        is_weapon = function.Name == "ValidateWeaponDefinition"
        inv_list.append(
            (save_manager.apply_replacements(params.DefinitionData, is_weapon), is_weapon)
        )
        return False

    unrealsdk.RunHook("WillowGame.WillowPlayerController.OnChestOpened", __name__, Block)
    unrealsdk.RunHook("WillowGame.WillowPlayerController.ValidateItemDefinition", __name__, ValidateItemWeaponDefinition)
    unrealsdk.RunHook("WillowGame.WillowPlayerController.ValidateWeaponDefinition", __name__, ValidateItemWeaponDefinition)

    caller.Open()

    unrealsdk.RemoveHook("WillowGame.WillowPlayerController.OnChestOpened", __name__)
    unrealsdk.RemoveHook("WillowGame.WillowPlayerController.ValidateItemDefinition", __name__)
    unrealsdk.RemoveHook("WillowGame.WillowPlayerController.ValidateWeaponDefinition", __name__)

    save_manager.write()
    caller.ChestIsOpen = True

    for def_data, is_weapon in inv_list:
        if is_weapon:
            caller.AddWeaponFromDef(def_data, False, False)
        else:
            caller.AddItemFromDef(def_data, False, False)

    """
    Technically we should get this function to return True, which should be doable by blocking more
    function calls and caching some stuff, but nothing that calls this function relies on that value
    anyway.
    """
    return False


@hook("WillowGame.WillowInventoryStorage.Close")
def Close(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
    PC = caller.Outer.GetOwningPlayerController()
    inv_manager = PC.GetPawnInventoryManager()

    save_name: str
    is_bank: bool
    if caller == inv_manager.TheBank:
        save_name = PC.SaveGameName
        is_bank = True
    elif caller == inv_manager.TheStash:
        save_name = STASH_NAME
        is_bank = False
    elif caller in (inv_manager.TheGrinder, inv_manager.TheMailBox):
        return True
    else:
        unrealsdk.Log("[SanitySaver] Could not identify opened container!")
        return True

    new_save = SaveManager(save_name, is_bank)
    existing_save = SaveManager(save_name, is_bank)
    existing_save.load()

    for chest_data in caller.TheChest:
        item = chest_data.Inventory
        if item is None or item.DefinitionData is None:
            continue

        new_save.add_item(
            item.DefinitionData,
            chest_data.InventoryClass.Name == "WillowWeapon",
            existing_save
        )

    new_save.write()

    return True
