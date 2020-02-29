import unrealsdk
import json
import os
import random
from os import path
from typing import Dict
from typing import List
from typing import NamedTuple
from typing import Optional
from typing import Tuple


# Simple data class to store the info we need about each seed
class SideMissionRandomizerSeed(NamedTuple):
    Seed: int
    Name: str


# This class just store the base info about the mod in a single place
class SideMissionRandomizerBase(unrealsdk.BL2MOD):
    Name: str = "Side Mission Randomizer"
    Author: str = "apple1417"
    Description: str = (
        "Randomizes the progression order of side missions."
    )
    Types: List[unrealsdk.ModTypes] = [unrealsdk.ModTypes.Gameplay]
    Version = "1.2"

    LOCAL_DIR: str = path.dirname(path.realpath(__file__))

    def __init__(self) -> None:
        # Hopefully I can remove this in a future SDK update
        self.Author += "\nVersion: " + str(self.Version)


# This class defines each individual mod for each seed
class SideMissionRandomizerChild(SideMissionRandomizerBase):
    def __init__(self, SMRSeed: SideMissionRandomizerSeed) -> None:
        super().__init__()

        self.SettingsInputs: Dict[str, str] = {
            "Enter": "Enable",
            "Delete": "Delete",
            "D": "Dump Progression"
        }

        self.SMRSeed = SMRSeed

        # If you don't define a name just use the actual seed
        seedName = self.SMRSeed.Name
        if len(seedName) == 0:
            seedName = str(self.SMRSeed.Seed)

        self.DUMP_PATH = path.join(self.LOCAL_DIR, f"{seedName}.txt")
        self.Name += f" ({seedName})"
        self.Description = (
            f"<font size='24' color='#FFDEAD'>SMR - {seedName}</font>\n"
            f"{self.Description}\n"
            "\n"
            f"Seed: {self.SMRSeed.Seed}"
        )

        rand = random.Random(SMRSeed.Seed)

        def randSample(array: List[unrealsdk.UObject]) -> List[unrealsdk.UObject]:
            amount = min(10, len(array), max(1, int(rand.normalvariate(3, 2))))
            return rand.sample(array, amount)

        # To generate the random tree:
        #  1. Select a few missions to be unlocked by default
        #  2. Select a random mission that hasn't been unlocked yet
        #  3. Set it's dependencies to be a random selection of the unlocked missions
        #  4. Add it to the unlocked set and loop
        lockedMissions = list(SMRParent.DefaultDependencies.keys())
        availibleMissions = randSample(lockedMissions) + randSample(lockedMissions)

        self.NewDependencies: Dict[unrealsdk.UObject, List[unrealsdk.UObject]] = {}
        for m in availibleMissions:
            lockedMissions.remove(m)
            self.NewDependencies[m] = []

        while len(lockedMissions) > 0:
            newMission = rand.choice(lockedMissions)
            lockedMissions.remove(newMission)

            self.NewDependencies[newMission] = randSample(availibleMissions)

            availibleMissions.append(newMission)

    def Enable(self) -> None:
        for mission in self.NewDependencies:
            mission.Dependencies = self.NewDependencies[mission]
            mission.ObjectiveDependency = (None, 0)

    def SettingsInputPressed(self, name: str) -> None:
        # Most of these pass through into the parent mod cause we only want to let one child be
        #  active at a time
        if name == "Enable":
            SMRParent.EnableChild(self)

        elif name == "Disable":
            SMRParent.DisableChild(self)

        elif name == "Delete":
            SMRParent.RemoveChild(self)

        elif name == "Dump Progression":
            self.DumpToFile()

    def DumpToFile(self) -> None:
        # Invert the map to show what each mission unlocks instead of dependencies
        # This is just a nicer sorting order
        unlockMap: Dict[str, List[str]] = {}
        for mission in self.NewDependencies:
            for dep in self.NewDependencies[mission]:
                if dep.MissionName in unlockMap:
                    unlockMap[dep.MissionName].append(mission.MissionName)
                else:
                    unlockMap[dep.MissionName] = [mission.MissionName]

        with open(self.DUMP_PATH, "w") as file:
            file.write(
                "# I recommend you put this into a grapher such as http://www.webgraphviz.com/\n\n"
            )
            for mission in sorted(unlockMap.keys()):
                for unlock in unlockMap[mission]:
                    file.write(f'"{mission}" -> "{unlock}"\n')

        os.startfile(self.DUMP_PATH)


# This class defines the single parent "Mod" that you use to create the child mods
class SideMissionRandomizerParent(SideMissionRandomizerBase):
    def __init__(self) -> None:
        super().__init__()
        self.SettingsInputs: Dict[str, str] = {
            "Enter": "Load"
        }

        # Workaround for not being able to use status
        self.Name += " - <font color='#FF0000'>Not Loaded</font>"

        self.Description = (
            f"<font size='24' color='#FFDEAD'>Side Mission Randomizer</font>\n"
            f"{self.Description}\n"
            "Note that after loading this mod you still need to enable it on a particular seed."
        )

        self.SEED_PATH: str = path.join(self.LOCAL_DIR, "seeds.json")

        self.CurrentlyEnabledChild: Optional[SideMissionRandomizerChild] = None
        self.SeedInfo: List[SideMissionRandomizerSeed] = []

    # This is essentially the disable function for all of the child mods
    def RevertMissionsToDefaults(self) -> None:
        for mission in self.DefaultDependencies:
            mission.Dependencies = self.DefaultDependencies[mission]
        for mission in self.DefaultObjectiveDependencies:
            mission.ObjectiveDependency = self.DefaultObjectiveDependencies[mission]

    def SettingsInputPressed(self, name: str) -> None:
        if name == "Load":
            self.SettingsInputs = {
                "R": "Reload From File",
                "N": "New Seed",
                "Delete": "Delete All",
                "O": "Open Seed File"
            }
            # self.Status = "<font color='#00FF00'>Loaded</font>"
            self.Status = "Enabled"
            self.Name = super().Name + " - <font color='#00FF00'>Loaded</font>"

            # Save the default mission dependencies, so that we're able to restore them
            # We can't do this in __init__() cause they're not all loaded at that point
            self.DefaultDependencies: Dict[unrealsdk.UObject, List[unrealsdk.UObject]] = {}
            self.DefaultObjectiveDependencies: Dict[unrealsdk.UObject, Tuple[unrealsdk.UObject, int]] = {}
            for mission in unrealsdk.FindAll("MissionDefinition"):
                # Filter out the default MissionDefinition and all main missions
                if mission.bPlotCritical or not mission.MissionName:
                    continue

                # Need to convert this to a list because the default FArray returned is a reference
                self.DefaultDependencies[mission] = list(mission.Dependencies)
                self.DefaultObjectiveDependencies[mission] = (
                    mission.ObjectiveDependency.Objective,
                    mission.ObjectiveDependency.Status
                )

            self.LoadFromFile()

        elif name == "Reload From File":
            self.LoadFromFile()

        elif name == "New Seed":
            seed = random.randrange(0xFFFFFFFF)
            SMRSeed = SideMissionRandomizerSeed(seed, str(seed))
            self.SeedInfo.append(SMRSeed)
            self.SaveSeedInfo()

            newMod = SideMissionRandomizerChild(SMRSeed)

            index = unrealsdk.Mods.index(self) + 1
            unrealsdk.Mods.insert(index, newMod)

            self.EnableChild(newMod)

        elif name == "Delete All":
            if path.exists(self.SEED_PATH):
                os.remove(self.SEED_PATH)
            self.LoadFromFile()

        elif name == "Open Seed File":
            if not path.exists(self.SEED_PATH):
                self.SaveSeedInfo()
            os.startfile(self.SEED_PATH)

    def LoadFromFile(self) -> None:
        # Clear out any existing mods in the list
        toRemove = set()
        for mod in unrealsdk.Mods:
            if isinstance(mod, SideMissionRandomizerChild):
                toRemove.add(mod)
        for mod in toRemove:
            unrealsdk.Mods.remove(mod)
        self.RevertMissionsToDefaults()
        self.CurrentlyEnabledChild = None

        # Create all of the child mods
        index = unrealsdk.Mods.index(self) + 1
        self.SeedInfo = self.LoadSeedInfo()
        for seed in self.SeedInfo:
            unrealsdk.Mods.insert(index, SideMissionRandomizerChild(seed))

    # Two helper functions to explicitly list the var names in the json dump
    def SaveSeedInfo(self) -> None:
        newInfo = []
        for entry in self.SeedInfo:
            newInfo.append({"Seed": entry.Seed, "Name": entry.Name})
        with open(self.SEED_PATH, "w") as file:
            json.dump(newInfo, file, indent=2)

    def LoadSeedInfo(self) -> List[SideMissionRandomizerSeed]:
        info = []
        if path.exists(self.SEED_PATH):
            with open(self.SEED_PATH) as file:
                for entry in json.load(file):
                    info.append(SideMissionRandomizerSeed(entry["Seed"], entry["Name"]))
        return info

    def EnableChild(self, child: SideMissionRandomizerChild) -> None:
        if self.CurrentlyEnabledChild is not None:
            self.DisableChild(self.CurrentlyEnabledChild)
        self.CurrentlyEnabledChild = child

        child.Status = "Enabled"
        child.SettingsInputs["Enter"] = "Disable"
        child.Enable()

    def DisableChild(self, child: SideMissionRandomizerChild) -> None:
        child.Status = "Disabled"
        child.SettingsInputs["Enter"] = "Enable"
        # Just in case for some reason this isn't the same as 'child'
        if self.CurrentlyEnabledChild is not None:
            self.CurrentlyEnabledChild.Status = "Disabled"
            self.CurrentlyEnabledChild.SettingsInputs["Enter"] = "Enable"

        self.CurrentlyEnabledChild = None
        self.RevertMissionsToDefaults()

    def RemoveChild(self, child: SideMissionRandomizerChild) -> None:
        if self.CurrentlyEnabledChild == child:
            self.DisableChild(child)
        unrealsdk.Mods.remove(child)

        self.SeedInfo.remove(child.SMRSeed)
        self.SaveSeedInfo()


SMRParent: SideMissionRandomizerParent = SideMissionRandomizerParent()
unrealsdk.RegisterMod(SMRParent)
