import unrealsdk
from typing import Dict

from . import ABCToggleableCheat, SDKHook


class InstantCooldown(ABCToggleableCheat):
    Name = "Instant Cooldown"
    KeybindName = "Toggle Instant Cooldown"

    def GetHooks(self) -> Dict[str, SDKHook]:
        # We can use the same simple function for both action and melee skills
        def StartActiveMeleeSkillCooldown(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if caller != unrealsdk.GetEngine().GamePlayers[0].Actor:
                return True
            return not self.IsOn

        return {
            "WillowGame.WillowPlayerController.StartActiveSkillCooldown": StartActiveMeleeSkillCooldown,
            "WillowGame.WillowPlayerController.StartMeleeSkillCooldown": StartActiveMeleeSkillCooldown,
        }
