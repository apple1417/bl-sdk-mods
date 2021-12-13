import unrealsdk
from typing import Any, ClassVar

from Mods.ModMenu import EnabledSaveType, Hook, Mods, ModTypes, Options, RegisterMod, SDKMod


class Mario(SDKMod):
    Name: str = "Mario Mode"
    Author: str = "apple1417"
    Description: str = (
        "Jump on enemies to actually kill them."
    )
    Version: str = "2.0"

    Types: ModTypes = ModTypes.Utility
    SaveEnabledState: EnabledSaveType = EnabledSaveType.LoadWithSettings

    JumpDamage: Options.Slider
    JumpDamageChampion: Options.Slider
    JumpDamageOnly: Options.Boolean

    Gravity: Options.Slider

    JumpHeight: Options.Slider
    JumpHeightAttr: unrealsdk.UObject
    JumpHeightModifier: unrealsdk.UObject

    MoveSpeed: Options.Slider
    MoveSpeedAttr: unrealsdk.UObject
    MoveSpeedModifier: unrealsdk.UObject

    PACKAGE_NAME: ClassVar[str] = "Mario"
    ATTR_PREFIX: ClassVar[str] = "Attr_"
    MODIFIER_PREFIX: ClassVar[str] = "Modifier_"
    JUMP_HEIGHT_SUFFIX: ClassVar[str] = "JumpHeight"
    MOVE_SPEED_SUFFIX: ClassVar[str] = "MoveSpeed"

    MOVE_SPEED_ATTRIBUTE_NAME: ClassVar[str] = "D_Attributes.GameplayAttributes.FootSpeed"

    def __init__(self) -> None:
        self.JumpDamage = Options.Slider(
            Caption="Jump Damage",
            Description=(
                "The percentage of enemy health jumping damage deals."
            ),
            StartingValue=50,
            MinValue=0,
            MaxValue=100,
            Increment=1
        )
        self.JumpDamageChampion = Options.Slider(
            Caption="Jump Damage (Champion)",
            Description=(
                "The percentage of enemy health jumping damage deals to champion enemies (generally"
                " badasses and bosses)."
            ),
            StartingValue=25,
            MinValue=0,
            MaxValue=100,
            Increment=1
        )
        self.JumpDamageOnly = Options.Boolean(
            Caption="Disable Other Damage",
            Description=(
                "If other forms of damage should do nothing, so you can only hurt enemies by"
                " jumping on them. May have side effects."
            ),
            StartingValue=False
        )

        self.JumpHeight = Options.Slider(
            Caption="Jump Height Scale",
            Description=(
                "Percent to adjust jump height by. Positive values increase height, negative"
                " decrease it, -50 means you jump 1 / (1 + 0.5) = 2/3 as high."
            ),
            StartingValue=50,
            MinValue=-500,
            MaxValue=500,
            Increment=1
        )
        self.MoveSpeed = Options.Slider(
            Caption="Movement Speed Scale",
            Description=(
                "Percent to adjust movement speed height by. Positive values increase speed"
                " negative decrease it, -50 means you run 1 / (1 + 0.5) = 2/3 as fast."
            ),
            StartingValue=50,
            MinValue=-500,
            MaxValue=500,
            Increment=1
        )

        self.Options = [
            self.JumpDamage,
            self.JumpDamageChampion,
            self.JumpDamageOnly,
            self.JumpHeight,
            self.MoveSpeed
        ]

        self.CreateObjects()

    def CreateObjects(self) -> None:
        PC = unrealsdk.GetEngine().GamePlayers[0].Actor

        package = unrealsdk.FindObject("Package", self.PACKAGE_NAME)
        if package is None:
            package = unrealsdk.ConstructObject(
                Class="Package",
                Outer=None,
                Name=self.PACKAGE_NAME,
            )
            unrealsdk.KeepAlive(package)

        # A Jump Height attribute doesn't exist in TPS(/AoDK?), so we need to create one ourselves
        self.JumpHeightAttr = unrealsdk.FindObject(
            "AttributeDefinition",
            self.PACKAGE_NAME + "." + self.ATTR_PREFIX + self.JUMP_HEIGHT_SUFFIX
        )
        if self.JumpHeightAttr is None:
            self.JumpHeightAttr = unrealsdk.ConstructObject(
                Class="AttributeDefinition",
                Outer=package,
                Name=self.ATTR_PREFIX + self.JUMP_HEIGHT_SUFFIX,
            )
            unrealsdk.KeepAlive(self.JumpHeightAttr)

            self.JumpHeightAttr.ContextResolverChain = [
                unrealsdk.ConstructObject(
                    Class="PawnAttributeContextResolver",
                    Outer=self.JumpHeightAttr,
                )
            ]
            self.JumpHeightAttr.ValueResolverChain = [
                unrealsdk.ConstructObject(
                    Class="ObjectPropertyAttributeValueResolver",
                    Outer=self.JumpHeightAttr,
                )
            ]

            value_resolver = self.JumpHeightAttr.ValueResolverChain[0]
            value_resolver.CachedProperty = unrealsdk.FindObject(
                "FloatAttributeProperty",
                "Engine.Pawn:JumpZ"
            )
            PC.ConsoleCommand(f"set {PC.PathName(value_resolver)} PropertyName JumpZ")

        self.JumpHeightModifier = unrealsdk.FindObject(
            "AttributeModifier",
            self.PACKAGE_NAME + "." + self.MODIFIER_PREFIX + self.JUMP_HEIGHT_SUFFIX
        )
        if self.JumpHeightModifier is None:
            self.JumpHeightModifier = unrealsdk.ConstructObject(
                Class="AttributeModifier",
                Outer=package,
                Name=self.MODIFIER_PREFIX + self.JUMP_HEIGHT_SUFFIX,
            )
            unrealsdk.KeepAlive(self.JumpHeightModifier)
            self.JumpHeightModifier.Type = 0  # MT_Scale
            self.JumpHeightModifier.Value = self.JumpHeight.CurrentValue / 100

        self.MoveSpeedAttr = unrealsdk.FindObject(
            "AttributeDefinition",
            self.MOVE_SPEED_ATTRIBUTE_NAME
        )

        self.MoveSpeedModifier = unrealsdk.FindObject(
            "AttributeModifier",
            self.PACKAGE_NAME + "." + self.MODIFIER_PREFIX + self.MOVE_SPEED_SUFFIX
        )
        if self.MoveSpeedModifier is None:
            self.MoveSpeedModifier = unrealsdk.ConstructObject(
                Class="AttributeModifier",
                Outer=package,
                Name=self.MODIFIER_PREFIX + self.MOVE_SPEED_SUFFIX,
            )
            unrealsdk.KeepAlive(self.MoveSpeedModifier)
            self.MoveSpeedModifier.Type = 0  # MT_Scale
            self.MoveSpeedModifier.Value = self.MoveSpeed.CurrentValue / 100

    @Hook("WillowGame.WillowAIPawn.TakeDamage")
    def TakeDamage(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
        if params.InstigatedBy is None:
            return True
        if params.InstigatedBy.Class.Name != "WillowPlayerController":
            return True
        if params.DamageType.Name != "DmgType_Crushed":
            return not self.JumpDamageOnly.CurrentValue
        if caller.WorldInfo.Game.IsFriendlyFire(caller, params.InstigatedBy.Pawn):
            return True

        multiplier: float
        if caller.BalanceDefinitionState.BalanceDefinition.Champion:
            multiplier = self.JumpDamageChampion.CurrentValue / 100
        else:
            multiplier = self.JumpDamage.CurrentValue / 100

        damage = (caller.GetMaxHealth() + caller.GetMaxShieldStrength()) * multiplier

        shield = caller.GetShieldStrength()
        if damage < shield:
            caller.SetShieldStrength(shield - damage)
            return True
        else:
            caller.SetShieldStrength(0)
            damage -= shield

        # If we set the health to 0, you don't get any xp. It's easiest to just set health to 0.5,
        #  and let this function continue to have the normal damage tick kill them.
        # In the case that the enemy has less than 0.5 health, we just kill them to avoid a loop.
        health = caller.GetHealth()
        if health < 0.5:
            caller.SetHealth(0)
        elif (health - damage) < 0.5:
            caller.SetHealth(0.5)
        else:
            caller.SetHealth(health - damage)

        return True

    @Hook("WillowGame.WillowPawn.PostBeginPlay")
    def WillowPawn_PostBeginPlay(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
        if caller.Class.Name == "WillowPlayerPawn":
            self.JumpHeightAttr.AddAttributeModifier(caller, self.JumpHeightModifier)
            self.MoveSpeedAttr.AddAttributeModifier(caller, self.MoveSpeedModifier)

        return True

    def ModOptionChanged(self, option: Options.Base, new_value: Any) -> None:
        if option in (self.JumpHeight, self.MoveSpeed):
            attr = {
                self.JumpHeight: self.JumpHeightAttr,
                self.MoveSpeed: self.MoveSpeedAttr
            }[option]  # type: ignore
            modifier = {
                self.JumpHeight: self.JumpHeightModifier,
                self.MoveSpeed: self.MoveSpeedModifier
            }[option]  # type: ignore

            modifier.Value = new_value / 100
            for pawn in unrealsdk.FindAll("WillowPlayerPawn"):
                attr.RemoveAttributeModifier(pawn, modifier)
                attr.AddAttributeModifier(pawn, modifier)


instance = Mario()
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
