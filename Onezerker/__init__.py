import unrealsdk
import math
from typing import ClassVar, Dict, List, Optional


class Onezerker(unrealsdk.BL2MOD):
    Name: ClassVar[str] = "Onezerker"
    Author: ClassVar[str] = "apple1417"
    Description: ClassVar[str] = (
        "Gunzerk with two copies of the same gun instead of two different ones."
    )
    Types: ClassVar[List[unrealsdk.ModTypes]] = [unrealsdk.ModTypes.Gameplay]
    Version: ClassVar[str] = "1.4"

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
            unrealsdk.Log("[Onezerker] Unable to find NumberWeaponsEquiped object, assuming loaded in TPS")
            self.Name = f"<font color='#ff0000'>{self.Name}</font>"  # type: ignore
            self.Description += "\n<font color='#ff0000'>Incompatible with TPS</font>"  # type: ignore
            self.SettingsInputs = {}
            self.NumWeapObj = None
        else:
            unrealsdk.KeepAlive(obj)
            self.NumWeapObj = obj

        self.WeaponMap = {}

    def DupeWeapon(self, weapon: unrealsdk.UObject) -> unrealsdk.UObject:
        """
          We save a map of existing duped weapons to try make sure you get the same one back
          For one this helps keep memory usage down, but more importantly it means when you switch
           back you'll have the same amount of ammo left in the mag - you can't get free offhand
           reloads just by switching to another gun + back
        """
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
            unrealsdk.Log("[Onezerker] Didn't load correctly, not enabling")
            self.Status = "Disabled"
            self.SettingsInputs = {}
            return

        # Called when you stop gunzerking
        def OnActionSkillEnded(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            # Reset the map so that you don't end up with partially used weapons next time you start
            #  (and to free up a bit of memory)
            self.WeaponMap = {}
            return True

        # Called when you start gunzerking
        def EquipInitialWeapons(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            PC = unrealsdk.GetEngine().GamePlayers[0].Actor
            if PC.Pawn is None:
                return False
            weap = PC.Pawn.Weapon
            if weap is None:
                return False

            # This is the only real bit of the function we overwrite
            weapAlt = self.DupeWeapon(weap)
            PC.Pawn.OffHandWeapon = weapAlt

            PC.Pawn.InvManager.SetCurrentWeapon(weap, False)
            PC.Pawn.InvManager.SetCurrentWeapon(weapAlt, True)
            weap.RefillClip()
            weapAlt.RefillClip()
            if PC.bInSprintState:
                caller.SetTimer(min(weap.GetEquipTime(), weapAlt.GetEquipTime()), False, "SprintTransition")
            caller.SetLeftSideControl()

            return False

        # Called when you try switch weapons while gunzerking using the scrollwheel/cycle weapon
        # Unfortuantly there are no arguments, so I can't tell if you scroll backwards
        def SwitchWeapons(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            Pawn = unrealsdk.GetEngine().GamePlayers[0].Actor.Pawn

            # Get the equiped weapon list in order
            weaponList = [None, None, None, None]
            weapon = Pawn.InvManager.InventoryChain
            while weapon is not None:
                weaponList[weapon.QuickSelectSlot - 1] = weapon
                weapon = weapon.Inventory
            # Usually you just swap both weapons, but here we'll go down the inventory in order
            index = Pawn.Weapon.QuickSelectSlot % 4
            while weaponList[index] is not None:
                index = (index + 1) % 4
            weapon = weaponList[index]

            weapAlt = self.DupeWeapon(weapon)
            Pawn.InvManager.SetCurrentWeapon(weapon, False)
            Pawn.InvManager.SetCurrentWeapon(weapAlt, True)
            caller.SetOffHandCrosshair(weapAlt)

            return False

        # Called when you try switch weapons while gunzerking using the number keys
        # This time we are given the weapon to switch too, which simplifies things
        def SwitchToWeapon(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            Pawn = unrealsdk.GetEngine().GamePlayers[0].Actor.Pawn

            if params.NewWeapon != Pawn.Weapon:
                Pawn.InvManager.SetCurrentWeapon(params.NewWeapon, False)

                weapAlt = self.DupeWeapon(params.NewWeapon)
                Pawn.InvManager.SetCurrentWeapon(weapAlt, True)
                caller.SetOffHandCrosshair(weapAlt)

            return False

        # Called when you return from the menu while gunzerking
        def BringWeaponsUpAfterPutDown(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            Pawn = unrealsdk.GetEngine().GamePlayers[0].Actor.Pawn

            # There is a function that *should* return this in list form, but it doesn't work properly so,
            #  we have to parse down the linked list instead
            weapon = Pawn.InvManager.InventoryChain
            while weapon is not None:
                if weapon.QuickSelectSlot == params.MainHandWeaponSlot:
                    break
                weapon = weapon.Inventory
            # If you dropped the equiped slot
            if weapon is None:
                weapon = Pawn.InvManager.InventoryChain

            caller.ForceRefreshSkills()
            caller.ClientBringWeaponsUpAfterPutDown(weapon, self.DupeWeapon(weapon))

            return False

        # Called whenever a "Behavior_RefillWeapon" is run, happens to only be when auto loader triggers
        def ApplyBehaviorToContext(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            # Remove from the weapon map so that it's remade with full ammo
            if params.ContextObject in self.WeaponMap:
                del self.WeaponMap[params.ContextObject]
            return True

        # Called whenever you try drop your active weapon
        def TossInventory(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            PC = unrealsdk.GetEngine().GamePlayers[0].Actor

            # If you're not currently gunzerking then don't bother doing anything special
            if PC.Pawn.MyActionSkill is None:
                return True

            if params.Inv == PC.Pawn.Weapon:
                # I can't properly call the built in functions for this so let's do a bunch of maths
                loc = PC.Pawn.Location
                rot = PC.Rotation
                vel = PC.Pawn.Velocity

                multi = math.pi / 0x7fff
                rotVect = (
                    math.cos(rot.Yaw * multi) * math.cos(rot.Pitch * multi),
                    math.sin(rot.Yaw * multi) * math.cos(rot.Pitch * multi),
                    math.sin(rot.Pitch * multi),
                )

                dot = (rotVect[0] * vel.X) + (rotVect[1] * vel.Y) + (rotVect[2] * vel.Z) + 100

                params.Inv.DropFrom((loc.X, loc.Y, loc.Z), (rotVect[0] * dot, rotVect[1] * dot, rotVect[2] * dot + 200))
            else:
                caller.super(PC.Pawn).TossInventory(params.Inv, params.ForceVelocity)

            # Unfortuantly this gets delayed but I need to know what weapon to dupe
            if PC.Pawn.Weapon is not None:
                PC.Pawn.InvManager.SetCurrentWeapon(self.DupeWeapon(PC.Pawn.Weapon), True)

            return False

        # Called when you get off of a ladder
        def EndClimbLadder(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            # Don't do anything special if this isn't our pawn or when not gunzerking
            if caller.MyActionSkill is None:
                return True

            # Recreate the rest of the function
            caller.Controller.EndClimbLadder()
            if caller.Controller.Physics == 9:
                caller.Controller.SetPhysics(1)
            caller.Controller.SetWeaponsRestricted(False, True)
            caller.SetCollision(caller.bCollideActors, True, caller.bIgnoreEncroachers)

            # Fix our offhand, this syncs up for once
            caller.InvManager.SetCurrentWeapon(self.DupeWeapon(caller.Controller.LastUsedWeapon), True)

            return False

        """
        Called whenever anyone:
         1. Picks up a weapon while having empty slots available
         2. Equips a new weapon in your inventory screen
         3. Force equip a new weapon
        Very conviniently, in case 3 alone the paramater "bDoNotActivate" is false
        """
        def ClientGivenTo(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            Pawn = unrealsdk.GetEngine().GamePlayers[0].Actor.Pawn

            # If you're not the one who called on, you didn't force equip, or you're not gunzerking
            #  then don't bother doing anything special
            if params.NewOwner != Pawn or params.bDoNotActivate or Pawn.MyActionSkill is None:
                return True

            # In contrast to dropping, unfortuantly this doesn't get delayed, there's no animation
            Pawn.InvManager.SetCurrentWeapon(self.DupeWeapon(caller), True)
            return True

        unrealsdk.RegisterHook("WillowGame.DualWieldActionSkill.OnActionSkillEnded", "Onezerker", OnActionSkillEnded)
        unrealsdk.RegisterHook("WillowGame.DualWieldActionSkill.EquipInitialWeapons", "Onezerker", EquipInitialWeapons)
        unrealsdk.RegisterHook("WillowGame.DualWieldActionSkill.SwitchWeapons", "Onezerker", SwitchWeapons)
        unrealsdk.RegisterHook("WillowGame.DualWieldActionSkill.SwitchToWeapon", "Onezerker", SwitchToWeapon)
        unrealsdk.RegisterHook("WillowGame.DualWieldActionSkill.BringWeaponsUpAfterPutDown", "Onezerker", BringWeaponsUpAfterPutDown)
        unrealsdk.RegisterHook("WillowGame.Behavior_RefillWeapon.ApplyBehaviorToContext", "Onezerker", ApplyBehaviorToContext)
        unrealsdk.RegisterHook("WillowGame.WillowPawn.TossInventory", "Onezerker", TossInventory)
        unrealsdk.RegisterHook("WillowGame.WillowPlayerPawn.EndClimbLadder", "Onezerker", EndClimbLadder)
        unrealsdk.RegisterHook("Engine.Weapon.ClientGivenTo", "Onezerker", ClientGivenTo)

        self.NumWeapObj.NumberOfWeapons = 1

    def Disable(self) -> None:
        unrealsdk.RemoveHook("WillowGame.DualWieldActionSkill.OnActionSkillEnded", "Onezerker")
        unrealsdk.RemoveHook("WillowGame.DualWieldActionSkill.EquipInitialWeapons", "Onezerker")
        unrealsdk.RemoveHook("WillowGame.DualWieldActionSkill.SwitchWeapons", "Onezerker")
        unrealsdk.RemoveHook("WillowGame.DualWieldActionSkill.SwitchToWeapon", "Onezerker")
        unrealsdk.RemoveHook("WillowGame.DualWieldActionSkill.BringWeaponsUpAfterPutDown", "Onezerker")
        unrealsdk.RemoveHook("WillowGame.Behavior_RefillWeapon.ApplyBehaviorToContext", "Onezerker")
        unrealsdk.RemoveHook("WillowGame.WillowPawn.TossInventory", "Onezerker")
        unrealsdk.RemoveHook("WillowGame.WillowPlayerPawn.EndClimbLadder", "Onezerker")
        unrealsdk.RemoveHook("Engine.Weapon.ClientGivenTo", "Onezerker")
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
