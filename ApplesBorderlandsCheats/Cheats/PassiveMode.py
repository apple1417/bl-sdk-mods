import unrealsdk
from typing import ClassVar

from . import ABCCycleableCheat


class PassiveMode(ABCCycleableCheat):
    Name = "Passive Enemies"
    KeybindName = "Cycle Passive Enemies"

    # These are in the same order as in the games's struct
    OFF: ClassVar[str] = "Off"  # Technically this is OPINION_Enemy
    NEUTRAL: ClassVar[str] = "Neutral"
    FRIENDLY: ClassVar[str] = "Friendly"
    AllValues = (OFF, NEUTRAL, FRIENDLY)

    def OnCycle(self) -> None:
        allegiance = unrealsdk.FindObject("PawnAllegiance", "GD_AI_Allegiance.Allegiance_Player")
        allegiance2 = unrealsdk.FindObject("PawnAllegiance", "GD_AI_Allegiance.Allegiance_Player_NoLevel")

        allegiance.bForceAllOtherOpinions = self.CurrentValue != PassiveMode.OFF
        allegiance2.bForceAllOtherOpinions = self.CurrentValue != PassiveMode.OFF

        allegiance.ForcedOtherOpinion = self.AllValues.index(self.CurrentValue)
        allegiance2.ForcedOtherOpinion = self.AllValues.index(self.CurrentValue)
