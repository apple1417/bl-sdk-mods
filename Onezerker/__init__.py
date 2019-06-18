import bl2sdk
import math

class Onezerker(bl2sdk.BL2MOD):
    Name = "Onezerker"
    Author = "apple1417"
    Description = (
        "Gunzerk with two copies of the same gun instead of two different ones."
    )
    Types = [bl2sdk.ModTypes.Gameplay]
    
    class LoggingLevel:
        NONE = 0
        CALLS = 1
        FULL = 2
    LOGGING = LoggingLevel.NONE
    
    numWeapObj = None
    previousNumWeap = 2
    
    def __init__(self):
        bl2sdk.LoadPackage("GD_Mercenary_Streaming_SF")
        obj = bl2sdk.FindObject("NumberWeaponsEquippedExpressionEvaluator", "GD_Mercenary_Skills.ActionSkill.Skill_Gunzerking:ExpressionTree_0.NumberWeaponsEquippedExpressionEvaluator_0")
        # Almost certainly because you tried to load this in TPS
        if obj == None:
            bl2sdk.Log("[Onezerker] Unable to find NumberWeaponsEquiped object, assuming loaded in TPS")
            self.Name = f"<font color='#ff0000'>{self.Name}</font>"
            self.Description += "\n<font color='#ff0000'>Incompatible with TPS</font>"
            self.SettingsInputs = {}
        else:
            bl2sdk.KeepAlive(obj)
            self.numWeapObj = obj
    
    def Enable(self):
        if self.numWeapObj == None:
            bl2sdk.Log("[Onezerker] Didn't load correctly, not enabling")
            return
        bl2sdk.RegisterHook("WillowGame.DualWieldActionSkill.EquipInitialWeapons", "Onezerker", EquipInitialWeapons)
        bl2sdk.RegisterHook("WillowGame.DualWieldActionSkill.SwitchToWeapon", "Onezerker", SwitchToWeapon)
        bl2sdk.RegisterHook("WillowGame.DualWieldActionSkill.BringWeaponsUpAfterPutDown", "Onezerker", BringWeaponsUpAfterPutDown)
        bl2sdk.RegisterHook("WillowGame.WillowPawn.TossInventory", "Onezerker", TossInventory)
        bl2sdk.RegisterHook("Engine.Weapon.ClientGivenTo", "Onezerker", ClientGivenTo)
        
        self.previousNumWeap = self.numWeapObj.NumberOfWeapons
        self.numWeapObj.NumberOfWeapons = 1
    
    def Disable(self):
        bl2sdk.RemoveHook("WillowGame.DualWieldActionSkill.EquipInitialWeapons", "Onezerker")
        bl2sdk.RemoveHook("WillowGame.DualWieldActionSkill.SwitchToWeapon", "Onezerker")
        bl2sdk.RemoveHook("WillowGame.DualWieldActionSkill.BringWeaponsUpAfterPutDown", "Onezerker")
        bl2sdk.RemoveHook("WillowGame.WillowPawn.TossInventory", "Onezerker")
        bl2sdk.RemoveHook("Engine.Weapon.ClientGivenTo", "Onezerker")
        if self.numWeapObj != None:
            self.numWeapObj.NumberOfWeapons = self.previousNumWeap
    
    def debugLogging(self, caller, function, params):
        if self.LOGGING == self.LoggingLevel.CALLS:
            bl2sdk.Log(str(function).split(".")[-1])
        elif self.LOGGING == self.LoggingLevel.FULL:
            bl2sdk.Log(str(caller))
            bl2sdk.Log(str(function))
            bl2sdk.Log(str(params))
    
    def dupeWeapon(self, weapon):
        newWeapon = weapon.CreateClone()
        newWeapon.AmmoPool.PoolManager = weapon.AmmoPool.PoolManager
        newWeapon.AmmoPool.PoolIndexInManager = weapon.AmmoPool.PoolIndexInManager
        newWeapon.AmmoPool.PoolGUID = weapon.AmmoPool.PoolGUID
        newWeapon.AmmoPool.Data = weapon.AmmoPool.Data
        newWeapon.InvManager = weapon.InvManager
        return newWeapon
    
    # Called when you start gunzerking
    def EquipInitialWeapons(self, caller, function, params):
        self.debugLogging(caller, function, params)
        
        PC = bl2sdk.GetEngine().GamePlayers[0].Actor
        if PC.Pawn == None:
            return
        weap = PC.Pawn.Weapon
        if weap == None:
            return
        
        # This is the only real bit of the function we overwrite
        weapAlt = self.dupeWeapon(weap)
        PC.Pawn.OffHandWeapon = weapAlt
        
        PC.Pawn.InvManager.SetCurrentWeapon(weap, False)
        PC.Pawn.InvManager.SetCurrentWeapon(weapAlt, True)
        weap.RefillClip()
        weapAlt.RefillClip()
        if PC.bInSprintState:
            caller.SetTimer(min(weap.GetEquipTime(), weapAlt.GetEquipTime()), False, "SprintTransition")
        caller.SetLeftSideControl()
    
    # Called when you return from the menu while gunzerking
    def BringWeaponsUpAfterPutDown(self, caller, function, params):
        self.debugLogging(caller, function, params)
        
        Pawn = bl2sdk.GetEngine().GamePlayers[0].Actor.Pawn
        
        # There is a function that *should* return this in list form, but it doesn't work properly so,
        #  we have to parse down the linked list instead
        weapon = Pawn.InvManager.InventoryChain
        while weapon != None:
            if weapon.QuickSelectSlot == params.MainHandWeaponSlot:
                break
            weapon = weapon.Inventory
        # If you dropped the equiped slot
        if weapon == None:
            weapon = Pawn.InvManager.InventoryChain
        
        caller.ForceRefreshSkills()
        caller.ClientBringWeaponsUpAfterPutDown(weapon, self.dupeWeapon(weapon))
    
    
    # Called when you try switch weapons while gunzerking
    def SwitchToWeapon(self, caller, function, params):
        self.debugLogging(caller, function, params)
        
        Pawn = bl2sdk.GetEngine().GamePlayers[0].Actor.Pawn
        
        if params.NewWeapon != Pawn.Weapon:
            Pawn.InvManager.SetCurrentWeapon(params.NewWeapon, False);
            
            weapAlt = self.dupeWeapon(params.NewWeapon)
            Pawn.InvManager.SetCurrentWeapon(weapAlt, True)
            caller.SetOffHandCrosshair(weapAlt);
    
    # Called whenever you try drop your active weapon
    def TossInventory(self, caller, function, params):
        self.debugLogging(caller, function, params)
        
        PC = bl2sdk.GetEngine().GamePlayers[0].Actor
        
        # If you're not currently gunzerking then don't bother doing anything special
        if PC.Pawn.MyActionSkill == None:
            return True
        
        if params.Inv == PC.Pawn.Weapon:
            # I can't properly call the built in functions for this so let's do a bunch of maths
            loc = PC.Pawn.Location
            rot = PC.Rotation
            vel = PC.Pawn.Velocity
            
            multi = math.pi/0x7fff
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
        PC.Pawn.InvManager.SetCurrentWeapon(self.dupeWeapon(PC.Pawn.Weapon), True)
    
    """
    Called whenever anyone:
     1. Picks up a weapon while having empty slots available
     2. Equips a new weapon in your inventory screen
     3. Force equip a new weapon
    Very conviniently, in case 3 alone the paramater "bDoNotActivate" is false
    """
    def ClientGivenTo(self, caller, function, params):
        self.debugLogging(caller, function, params)
        
        Pawn = bl2sdk.GetEngine().GamePlayers[0].Actor.Pawn
        
        # If you're not the one who called on, you didn't force equip, or you're not gunzerking
        #  then don't bother doing anything special
        if params.NewOwner != Pawn or params.bDoNotActivate or Pawn.MyActionSkill == None:
            return True
        
        # In contrast to dropping, unfortuantly this doesn't get delayed, there's no animation
        Pawn.InvManager.SetCurrentWeapon(self.dupeWeapon(caller), True)
        return True

def EquipInitialWeapons(caller: bl2sdk.UObject, function: bl2sdk.UFunction, params: bl2sdk.FStruct) -> bool:
    return instance.EquipInitialWeapons(caller, function, params)

def BringWeaponsUpAfterPutDown(caller: bl2sdk.UObject, function: bl2sdk.UFunction, params: bl2sdk.FStruct) -> bool:
    return instance.BringWeaponsUpAfterPutDown(caller, function, params)

def SwitchToWeapon(caller: bl2sdk.UObject, function: bl2sdk.UFunction, params: bl2sdk.FStruct) -> bool:
    return instance.SwitchToWeapon(caller, function, params)

def TossInventory(caller: bl2sdk.UObject, function: bl2sdk.UFunction, params: bl2sdk.FStruct) -> bool:
    return instance.TossInventory(caller, function, params)

def ClientGivenTo(caller: bl2sdk.UObject, function: bl2sdk.UFunction, params: bl2sdk.FStruct) -> bool:
    return instance.ClientGivenTo(caller, function, params)

instance = Onezerker()
if __name__ == "__main__":
    for mod in bl2sdk.Mods:
        if mod.Name == instance.Name:
            mod.Disable()
            bl2sdk.Mods.remove(mod)
            break
    
    instance.Enable()
bl2sdk.Mods.append(instance)
