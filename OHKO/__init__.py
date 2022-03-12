import unrealsdk

from Mods.ModMenu import EnabledSaveType, Hook, Mods, ModTypes, Options, RegisterMod, SDKMod


class OHKO(SDKMod):
    Name: str = "One-Hit KO"
    Author: str = "apple1417"
    Description: str = (
        "Makes you die in one hit."
    )
    Version: str = "1.0"

    Types: ModTypes = ModTypes.Gameplay
    SaveEnabledState: EnabledSaveType = EnabledSaveType.LoadWithSettings

    SkipFFYL: Options.Boolean
    OneHitEnemies: Options.Boolean

    def __init__(self) -> None:
        self.SkipFFYL = Options.Boolean(
            Caption="Skip FFYL",
            Description="When you take damage, you will instantly respawn, skipping FFYL.",
            StartingValue=False
        )
        self.OneHitEnemies = Options.Boolean(
            Caption="One-Hit Enemies",
            Description="Make players also one-hit enemies.",
            StartingValue=False
        )
        self.Options = [self.SkipFFYL, self.OneHitEnemies]

    @Hook("WillowGame.WillowPlayerPawn.TakeDamage")
    def PlayerTakeDamage(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
        if self.SkipFFYL.CurrentValue:
            caller.Controller.CausePlayerDeath(True)
        else:
            caller.SetHealth(0)

        return True

    @Hook("WillowGame.WillowAIPawn.TakeDamage")
    @Hook("WillowGame.WillowVehicle.TakeDamage")
    def EnemyTakeDamage(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
        if not self.OneHitEnemies.CurrentValue:
            return True
        if params.InstigatedBy.Class.Name != "WillowPlayerController":
            return True
        if params.InstigatedBy.WorldInfo.Game.IsFriendlyFire(caller, params.InstigatedBy.Pawn):
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


instance = OHKO()
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
