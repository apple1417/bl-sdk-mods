import unrealsdk
from typing import ClassVar, List

from . import ABCCheat


class TPFastTravel(ABCCheat):
    Name = "Teleport Between Fast Travel Stations"
    KeybindName = "Teleport Between Fast Travel Stations"

    TPClass: ClassVar[str] = "FastTravelStation"

    LastTravelIndex: int
    AllTravels: List[str]

    def __init__(self) -> None:
        self.LastTravelIndex = 0
        self.AllTravels = ["DUMMY"]

    def OnPress(self) -> None:
        # Get the list of all station names in the world
        currentTravels = []
        for obj in unrealsdk.FindAll(self.TPClass):
            if obj.TravelDefinition is None:
                continue
            currentTravels.append(obj.TravelDefinition.Name)

        # If the current station is not in the list then we must have changed worlds
        if self.AllTravels[self.LastTravelIndex] not in currentTravels:
            # Set to -1 so that it advances to the first one
            self.LastTravelIndex = -1
            self.AllTravels = currentTravels

        if len(self.AllTravels) == 0:
            return

        self.LastTravelIndex = (self.LastTravelIndex + 1) % len(self.AllTravels)
        station = self.AllTravels[self.LastTravelIndex]
        unrealsdk.GetEngine().GamePlayers[0].Actor.TeleportPlayerToStation(station)


class TPLevelTravel(TPFastTravel):
    Name = "Teleport Between Level Transitions"
    KeybindName = "Teleport Between Level Transitions"

    TPClass = "LevelTravelStation"
