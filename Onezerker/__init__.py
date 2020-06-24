import unrealsdk
from typing import ClassVar, Dict, List, Optional


class Onezerker(unrealsdk.BL2MOD):
    Name: ClassVar[str] = "Onezerker"
    Author: ClassVar[str] = "apple1417"
    Description: ClassVar[str] = (
        "Gunzerk with two copies of the same gun instead of two different ones."
    )
    Types: ClassVar[List[unrealsdk.ModTypes]] = [unrealsdk.ModTypes.Gameplay]
    Version: ClassVar[str] = "1.6"

    SettingsInputs: Dict[str, str]

    NumWeapObj: Optional[unrealsdk.UObject]
    WeaponMap: Dict[unrealsdk.UObject, unrealsdk.UObject]

    def __init__(self) -> None:
        # Hopefully I can remove this in a future SDK update
        self.Author += "\nVersion: " + str(self.Version)  # type: ignore

        unrealsdk.LoadPackage("GD_Mercenary_Streaming_SF")
        obj = unrealsdk.FindObject("NumberWeaponsEquippedExpressionEvaluator", "GD_Mercenary_Skills.ActionSkill.Skill_Gunzerking:ExpressionTree_0.NumberWeaponsEquippedExpressionEvaluator_0")

        # Almost certainly because you tried to load this in TPS
        if obj is None:
            unrealsdk.Log(f"[{self.Name}] Unable to find NumberWeaponsEquiped object, assuming loaded in TPS")
            self.Name = f"<font color='#ff0000'>{self.Name}</font>"  # type: ignore
            self.Description += "\n<font color='#ff0000'>Incompatible with TPS</font>"  # type: ignore
            self.SettingsInputs = {}
            self.NumWeapObj = None
        else:
            unrealsdk.KeepAlive(obj)
            self.NumWeapObj = obj

        self.WeaponMap = {}

    def DupeWeapon(self, weapon: unrealsdk.UObject) -> unrealsdk.UObject:
        # We keep a map of duped weapons so that swapping doesn't reload them
        if weapon in self.WeaponMap:
            return self.WeaponMap[weapon]

        newWeapon = weapon.CreateClone()
        newWeapon.AmmoPool.PoolManager = weapon.AmmoPool.PoolManager
        newWeapon.AmmoPool.PoolIndexInManager = weapon.AmmoPool.PoolIndexInManager
        newWeapon.AmmoPool.PoolGUID = weapon.AmmoPool.PoolGUID
        newWeapon.AmmoPool.Data = weapon.AmmoPool.Data
        newWeapon.InvManager = weapon.InvManager

        self.WeaponMap[weapon] = newWeapon
        return newWeapon

    def Enable(self) -> None:
        if self.NumWeapObj is None:
            unrealsdk.Log(f"[{self.Name}] Didn't load correctly, not enabling")
            self.Status = "Disabled"
            self.SettingsInputs = {}
            return

        def OnActionSkillEnded(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if caller.MyWillowPC != unrealsdk.GetEngine().GamePlayers[0].Actor:
                return True

            self.WeaponMap = {}
            return True

        def EquipInitialWeapons(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if caller.MyWillowPC != unrealsdk.GetEngine().GamePlayers[0].Actor:
                return True

            if caller.MyWillowPawn is None:
                return True
            weap = caller.MyWillowPawn.Weapon
            if weap is None:
                return False

            # This is the only real bit of the function we overwrite
            weapAlt = self.DupeWeapon(weap)
            caller.MyWillowPawn.OffHandWeapon = weapAlt

            caller.MyWillowPawn.InvManager.SetCurrentWeapon(weap, False)
            caller.MyWillowPawn.InvManager.SetCurrentWeapon(weapAlt, True)
            weap.RefillClip()
            weapAlt.RefillClip()
            if caller.MyWillowPC.bInSprintState:
                caller.SetTimer(min(weap.GetEquipTime(), weapAlt.GetEquipTime()), False, "SprintTransition")
            caller.SetLeftSideControl()

            return False

        # Called when switching weapons by scrolling/controller quick switch
        def NextWeapon(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            return ScrollWeapons(caller, True)

        def PrevWeapon(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            return ScrollWeapons(caller, False)

        def ScrollWeapons(caller: unrealsdk.UObject, next: bool) -> bool:
            pawn = unrealsdk.GetEngine().GamePlayers[0].Actor.Pawn
            if caller.Owner != pawn:
                return True

            if pawn.MyActionSkill is None:
                return True
            if pawn.MyActionSkill.Class.Name != "DualWieldActionSkill":
                return True

            weaponList = [None, None, None, None]
            weapon = pawn.InvManager.InventoryChain
            while weapon is not None:
                weaponList[weapon.QuickSelectSlot - 1] = weapon
                weapon = weapon.Inventory

            # Don't think this could actually happen but to be safe
            if weaponList.count(None) >= 4:
                return True

            index = pawn.Weapon.QuickSelectSlot - 1
            if next:
                index = (index + 1) % 4
                while weaponList[index] is None:
                    index = (index + 1) % 4
            else:
                index = (index - 1) % 4
                while weaponList[index] is None:
                    index = (index - 1) % 4
            weapon = weaponList[index]

            weapAlt = self.DupeWeapon(weapon)
            pawn.InvManager.SetCurrentWeapon(weapon, False)
            pawn.InvManager.SetCurrentWeapon(weapAlt, True)
            pawn.MyActionSkill.SetOffHandCrosshair(weapAlt)

            return False

        # Called when switching weapons (while gunzerking) using the number keys/dpad
        def SwitchToWeapon(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if caller.MyWillowPC != unrealsdk.GetEngine().GamePlayers[0].Actor:
                return True

            if params.NewWeapon != caller.MyWillowPawn.Weapon:
                caller.MyWillowPawn.InvManager.SetCurrentWeapon(params.NewWeapon, False)

                weapAlt = self.DupeWeapon(params.NewWeapon)
                caller.MyWillowPawn.InvManager.SetCurrentWeapon(weapAlt, True)
                caller.SetOffHandCrosshair(weapAlt)

            return False

        # Called on exiting menus
        def BringWeaponsUpAfterPutDown(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if caller.MyWillowPC != unrealsdk.GetEngine().GamePlayers[0].Actor:
                return True

            weapon = caller.MyWillowPawn.InvManager.InventoryChain
            while weapon is not None:
                if weapon.QuickSelectSlot == params.MainHandWeaponSlot:
                    break
                weapon = weapon.Inventory

            # If you dropped the equiped slot default to the start of the list - not sure if other
            #  behaviour might be better?
            if weapon is None:
                weapon = caller.MyWillowPawn.InvManager.InventoryChain
                # If you dropped all weapons just let the game handle it
                if weapon is None:
                    return True

            caller.ForceRefreshSkills()
            caller.ClientBringWeaponsUpAfterPutDown(weapon, self.DupeWeapon(weapon))

            return False

        def ApplyBehaviorToContext(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            """
            The only `Behavior_RefillWeapon` is auto loader - this is only called when it triggers

            All the other hooks guarentee that items only get duplicated if they're from the local
             player, so we can assume that if an item is in the map, the local player owns it.

            Auto loader only reloads unequipped weapons, so we can also guarentee that you will have
             to go through one of the other hooks to switch back to it.
            Because of this we can just remove the object from the map, it'll get recreated.
            For some reason just replicating the `.RefillClip()` call doesn't work.

            Now this might break if you do inventory merging, but really that's kinda on you.
            """
            if params.ContextObject in self.WeaponMap:
                del self.WeaponMap[params.ContextObject]
            return True

        # These two are identical except for the bit where I re-call the hooked function
        # I wish there was a neat way to merge them
        def TossInventory(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            pawn = unrealsdk.GetEngine().GamePlayers[0].Actor.Pawn
            if caller != pawn:
                return True
            if pawn.MyActionSkill is None:
                return True
            if pawn.MyActionSkill.Class.Name != "DualWieldActionSkill":
                return True

            unrealsdk.DoInjectedCallNext()
            caller.TossInventory(
                params.Inv,
                (params.ForceVelocity.X, params.ForceVelocity.Y, params.ForceVelocity.Z)
            )

            if pawn.Weapon is not None:
                pawn.InvManager.SetCurrentWeapon(self.DupeWeapon(pawn.Weapon), True)

            return False

        def EndClimbLadder(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            pawn = unrealsdk.GetEngine().GamePlayers[0].Actor.Pawn
            if caller != pawn:
                return True
            if pawn.MyActionSkill is None:
                return True
            if pawn.MyActionSkill.Class.Name != "DualWieldActionSkill":
                return True

            unrealsdk.DoInjectedCallNext()
            caller.EndClimbLadder(params.OldLadder)

            if pawn.Weapon is not None:
                pawn.InvManager.SetCurrentWeapon(self.DupeWeapon(pawn.Weapon), True)

            return False

        """
        Called whenever anyone:
         1. Picks up a weapon while having empty slots available
         2. Equips a new weapon in your inventory screen
         3. Force equip a new weapon
        Very conviniently, in case 3 alone the paramater "bDoNotActivate" is false
        """
        def ClientGivenTo(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            pawn = unrealsdk.GetEngine().GamePlayers[0].Actor.Pawn
            if params.NewOwner != pawn:
                return True
            if params.bDoNotActivate:
                return True
            if pawn.MyActionSkill is None:
                return True
            if pawn.MyActionSkill.Class.Name != "DualWieldActionSkill":
                return True

            pawn.InvManager.SetCurrentWeapon(self.DupeWeapon(caller), True)
            return True

        unrealsdk.RegisterHook("WillowGame.DualWieldActionSkill.OnActionSkillEnded", self.Name, OnActionSkillEnded)
        unrealsdk.RegisterHook("WillowGame.DualWieldActionSkill.EquipInitialWeapons", self.Name, EquipInitialWeapons)
        unrealsdk.RegisterHook("WillowGame.WillowInventoryManager.NextWeapon", self.Name, NextWeapon)
        unrealsdk.RegisterHook("WillowGame.WillowInventoryManager.PrevWeapon", self.Name, PrevWeapon)
        unrealsdk.RegisterHook("WillowGame.DualWieldActionSkill.SwitchToWeapon", self.Name, SwitchToWeapon)
        unrealsdk.RegisterHook("WillowGame.DualWieldActionSkill.BringWeaponsUpAfterPutDown", self.Name, BringWeaponsUpAfterPutDown)
        unrealsdk.RegisterHook("WillowGame.Behavior_RefillWeapon.ApplyBehaviorToContext", self.Name, ApplyBehaviorToContext)
        unrealsdk.RegisterHook("WillowGame.WillowPawn.TossInventory", self.Name, TossInventory)
        unrealsdk.RegisterHook("WillowGame.WillowPlayerPawn.EndClimbLadder", self.Name, EndClimbLadder)
        unrealsdk.RegisterHook("Engine.Weapon.ClientGivenTo", self.Name, ClientGivenTo)

        self.NumWeapObj.NumberOfWeapons = 1

    def Disable(self) -> None:
        unrealsdk.RemoveHook("WillowGame.DualWieldActionSkill.OnActionSkillEnded", self.Name)
        unrealsdk.RemoveHook("WillowGame.DualWieldActionSkill.EquipInitialWeapons", self.Name)
        unrealsdk.RemoveHook("WillowGame.WillowInventoryManager.NextWeapon", self.Name)
        unrealsdk.RemoveHook("WillowGame.WillowInventoryManager.PrevWeapon", self.Name)
        unrealsdk.RemoveHook("WillowGame.DualWieldActionSkill.SwitchToWeapon", self.Name)
        unrealsdk.RemoveHook("WillowGame.DualWieldActionSkill.BringWeaponsUpAfterPutDown", self.Name)
        unrealsdk.RemoveHook("WillowGame.Behavior_RefillWeapon.ApplyBehaviorToContext", self.Name)
        unrealsdk.RemoveHook("WillowGame.WillowPawn.TossInventory", self.Name)
        unrealsdk.RemoveHook("WillowGame.WillowPlayerPawn.EndClimbLadder", self.Name)
        unrealsdk.RemoveHook("Engine.Weapon.ClientGivenTo", self.Name)

        if self.NumWeapObj is not None:
            self.NumWeapObj.NumberOfWeapons = 2


instance = Onezerker()
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
