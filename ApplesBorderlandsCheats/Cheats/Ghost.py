import unrealsdk
from typing import ClassVar, Dict

from . import ABCToggleableCheat, SDKHook


class Ghost(ABCToggleableCheat):
    Name = "Ghost Mode"
    KeybindName = "Toggle Ghost Mode"

    MinSpeed: ClassVar[int] = 100
    DefaultSpeed: ClassVar[int] = 2500
    MaxSpeed: ClassVar[int] = 100000
    SpeedIncrement: ClassVar[float] = 1.2

    Pawn: unrealsdk.UObject
    IsInGhost: bool

    def __init__(self) -> None:
        super().__init__()
        self.IsInGhost = False

    def OnCycle(self) -> None:
        pc = unrealsdk.GetEngine().GamePlayers[0].Actor

        # Keeping track of ghost state seperatly incase you change it in a preset
        if self.IsOn and not self.IsInGhost:
            # We need to save the pawn so that we can possess the right one again later
            self.Pawn = pc.Pawn

            pc.ServerSpectate()
            pc.bCollideWorld = False
            pc.SpectatorCameraSpeed = self.DefaultSpeed

            self.IsInGhost = True
        elif not self.IsOn and self.IsInGhost:
            self.Pawn.Location = (pc.Location.X, pc.Location.Y, pc.Location.Z)
            pc.Possess(self.Pawn, True)

            self.IsInGhost = False

    def GetHooks(self) -> Dict[str, SDKHook]:
        # Turn off on map change
        def WillowClientDisableLoadingMovie(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            self.IsOn = False
            self.IsInGhost = False
            return True

        # Let scrolling adjust your movement speed
        def InputKey(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if params.Event != 0:
                return True

            pc = unrealsdk.GetEngine().GamePlayers[0].Actor
            speed = pc.SpectatorCameraSpeed

            if params.key == "MouseScrollUp":
                pc.SpectatorCameraSpeed = min(speed * self.SpeedIncrement, self.MaxSpeed)
            elif params.key == "MouseScrollDown":
                pc.SpectatorCameraSpeed = max(speed / self.SpeedIncrement, self.MinSpeed)

            return True

        return {
            "WillowGame.WillowPlayerController.WillowClientDisableLoadingMovie": WillowClientDisableLoadingMovie,
            "WillowGame.WillowUIInteraction.InputKey": InputKey
        }
