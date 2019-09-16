import bl2sdk
import json
import random
import os
from os import path
from typing import Dict
from typing import List
from typing import Optional
from typing import NamedTuple


# Simple data class to store the info we need about each seed
class SideMissionRandomizerSeed(NamedTuple):
    Seed: int
    Name: str


# This class just store the base info about the mod in a single place
class SideMissionRandomizerBase(bl2sdk.BL2MOD):
    Name: str = "Side Mission Randomizer"
    Author: str = "apple1417"
    Description: str = (
        "Randomizes the progression order of side missions."
    )
    Types: List[bl2sdk.ModTypes] = [bl2sdk.ModTypes.Gameplay]
    Version = "1.0"

    LOCAL_DIR: str = path.dirname(path.realpath(__file__))

    def __init__(self) -> None:
        # Hopefully I can remove this in a future SDK update
        self.Author += "\nVersion: " + str(self.Version)


# This class defines each individual mod for each seed
class SideMissionRandomizerChild(SideMissionRandomizerBase):
    SettingsInputs: Dict[str, str] = {
        "Enter": "Enable",
        "Delete": "Delete",
        "D": "Dump Progression"
    }

    DUMP_PATH: str
    NewDependencies: Dict[bl2sdk.UObject, List[bl2sdk.UObject]] = {}
    SMRSeed: SideMissionRandomizerSeed

    def GetSeedName(self) -> str:
        if len(self.SMRSeed.Name) == 0:
            return str(self.SMRSeed.Seed)
        return self.SMRSeed.Name

    def __init__(self, SMRSeed: SideMissionRandomizerSeed) -> None:
        super().__init__()

        self.SMRSeed = SMRSeed

        self.DUMP_PATH = path.join(self.LOCAL_DIR, self.GetSeedName() + ".txt")
        self.Name += f" ({self.GetSeedName()})"

        rand = random.Random(SMRSeed.Seed)
        def randSample(array: List[bl2sdk.UObject]) -> List[bl2sdk.UObject]:
            amount = min(10, len(array), max(0, int(rand.normalvariate(2, 4))))
            return rand.sample(array, amount)

        missions = list(SMRParent.DefaultDependencies.keys())
        availibleMissions = randSample(missions)
        for m in availibleMissions:
            missions.remove(m)

        while len(missions) > 0:
            newMission = rand.choice(missions)
            missions.remove(newMission)

            self.NewDependencies[newMission] = randSample(availibleMissions)

            availibleMissions.append(newMission)

    def Enable(self) -> None:
        for mission in self.NewDependencies:
            pass #mission.Dependencies = self.NewDependencies[mission]

    def SettingsInputPressed(self, name: str) -> None:
        if name == "Enable":
            SMRParent.EnableChild(self)

        elif name == "Disable":
            SMRParent.DisableChild(self)

        elif name == "Delete":
            SMRParent.RemoveChild(self)

        elif name == "Dump Progression":
            self.DumpToFile()

    def DumpToFile(self) -> None:
        # Invert the map to show what each mission unlocks instead of Dependencies
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
    SettingsInputs: Dict[str, str]  = {
        "Enter": "Load"
    }
    # SDK *says* it'd let me do this but it doesn't actually, it's forced to Enabled/Disabled
    # Status: str = "<font color='#FF0000'>Not Loaded</font>"

    CurrentlyEnabledChild: Optional[SideMissionRandomizerChild] = None
    DefaultDependencies: Dict[bl2sdk.UObject, List[bl2sdk.UObject]] = {}
    SEED_PATH: str

    def __init__(self) -> None:
        super().__init__()
        # Workaround for not being able to use status
        self.Name += " - <font color='#FF0000'>Not Loaded</font>"

        self.Description += (
            "\nNote that after loading this mod you still need to enable it on a particular seed."
        )

        self.SEED_PATH = path.join(self.LOCAL_DIR, "seeds.json")

    def RevertMissionsToDefaults(self) -> None:
        for mission in self.DefaultDependencies:
            pass #mission.Dependencies = self.DefaultDependencies[mission]

    def SettingsInputPressed(self, name: str) -> None:
        if name == "Load":
            self.SettingsInputs = {
                "Enter": "New Seed",
                "Delete": "Delete All",
                "R": "Reload From File",
                "O": "Open Seed File"
            }
            # self.Status = "<font color='#00FF00'>Loaded</font>"
            self.Status = "Enabled"
            self.Name = super().Name + " - <font color='#00FF00'>Loaded</font>"

            self.LoadFromFile()

            # Save the default mission Dependencies, so that we're able to restore them
            for mission in bl2sdk.FindAll("MissionDefinition"):
                # Filter out the default MissionDefinition and all main missions
                if mission.bPlotCritical or not mission.MissionName:
                    continue

                self.DefaultDependencies[mission] = mission.Dependencies

        elif name == "New Seed":
            if self.CurrentlyEnabledChild is not None:
                self.DisableChild(self.CurrentlyEnabledChild)

            SMRSeed = SideMissionRandomizerSeed(random.randrange(0xFFFFFFFF), "")
            self.SeedInfo.append(SMRSeed)
            with open(self.SEED_PATH, "w") as file:
                json.dump(self.SeedInfo, file, indent=2)

            self.CurrentlyEnabledChild = SideMissionRandomizerChild(SMRSeed)
            self.CurrentlyEnabledChild.Enable()

            index = bl2sdk.Mods.index(self) + 1
            bl2sdk.Mods.insert(index, self.CurrentlyEnabledChild);

        elif name == "Delete All":
            if path.exists(self.SEED_PATH):
                os.remove(self.SEED_PATH)
            self.LoadFromFile()

        elif name == "Reload From File":
            self.LoadFromFile()

        elif name == "Open Seed File":
            os.startfile(self.SEED_PATH)

    SeedInfo: List[SideMissionRandomizerSeed]
    def LoadFromFile(self) -> None:
        # Clear out any existing mods in the list
        for mod in bl2sdk.Mods:
            if isinstance(mod, SideMissionRandomizerChild):
                bl2sdk.Mods.remove(mod)
        self.RevertMissionsToDefaults()
        self.CurrentlyEnabledChild = None

        # Load from the file
        self.SeedInfo = []
        if path.exists(self.SEED_PATH):
            with open(self.SEED_PATH) as file:
                for entry in json.load(file):
                    self.SeedInfo.append(SideMissionRandomizerSeed(*entry))

        # Create all of the child mods
        index = bl2sdk.Mods.index(self) + 1
        for seed in self.SeedInfo:
            bl2sdk.Mods.insert(index, SideMissionRandomizerChild(seed))

    def EnableChild(self, child: SideMissionRandomizerChild) -> None:
        if self.CurrentlyEnabledChild is not None:
            self.DisableChild(self.CurrentlyEnabledChild)
        self.CurrentlyEnabledChild = child

        bl2sdk.Log(child.Name)

        child.Status = "Enabled"
        child.SettingsInputs["Enter"] = "Disable"
        # child.Enable()

    def DisableChild(self, child: SideMissionRandomizerChild) -> None:
        if self.CurrentlyEnabledChild is None:
            bl2sdk.Log((
                f"[SMR] Child '{child.Name}' requested to be disabled, but no child is currently"
                 " stored as enabled"
            ))
        elif self.CurrentlyEnabledChild != child:
            bl2sdk.Log((
                f"[SMR] Child '{child.Name}' requested to be disabled, but is not the child stored"
                f" as currently enabled, '{self.CurrentlyEnabledChild.Name}'"
            ))
            self.CurrentlyEnabledChild.Status = "Disabled"
            self.CurrentlyEnabledChild.SettingsInputs["Enter"] = "Enable"

        self.CurrentlyEnabledChild = None
        self.RevertMissionsToDefaults()

        child.Status = "Disabled"
        child.SettingsInputs["Enter"] = "Enable"

    def RemoveChild(self, child: SideMissionRandomizerChild) -> None:
        if self.CurrentlyEnabledChild == child:
            self.DisableChild(child)
        bl2sdk.Mods.remove(child)

        self.SeedInfo.remove(child.SMRSeed)
        with open(self.SEED_PATH, "w") as file:
            json.dump(self.SeedInfo, file, indent=2)

SMRParent: SideMissionRandomizerParent = SideMissionRandomizerParent()
bl2sdk.Mods.append(SMRParent)
