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
    def __init__(self, SMRSeed: SideMissionRandomizerSeed) -> None:
        super().__init__()

        self.SettingsInputs: Dict[str, str] = {
            "Enter": "Enable",
            "Delete": "Delete",
            "D": "Dump Progression"
        }

        self.SMRSeed = SMRSeed

        seedName = self.SMRSeed.Name
        if len(seedName) == 0:
            seedName = str(self.SMRSeed.Seed)

        self.DUMP_PATH = path.join(self.LOCAL_DIR, f"{seedName}.txt")
        self.Name += f" {seedName}"
        self.Description = (
            f"<font size='24' color='#FFDEAD'>SMR - {seedName}</font>\n"
            f"{self.Description}"
        )

        rand = random.Random(SMRSeed.Seed)
        def randSample(array: List[bl2sdk.UObject]) -> List[bl2sdk.UObject]:
            amount = min(10, len(array), max(0, int(rand.normalvariate(2, 4))))
            return rand.sample(array, amount)

        missions = list(SMRParent.DefaultMissions)
        availibleMissions = randSample(missions)

        self.NewDependencies: Dict[bl2sdk.UObject, bl2sdk.FArray] = {}
        for m in availibleMissions:
            missions.remove(m)
            self.NewDependencies[m] = []

        while len(missions) > 0:
            newMission = rand.choice(missions)
            missions.remove(newMission)

            bl2sdk.Log(str(type(newMission)))

            self.NewDependencies[newMission] = randSample(availibleMissions)

            availibleMissions.append(newMission)

    def Enable(self) -> None:
        for mission in self.NewDependencies:
            bl2sdk.Log(f"{mission}: {self.NewDependencies[mission]}")
            bl2sdk.Log(f"{type(mission)}, {type(self.NewDependencies[mission])}")
            mission.Dependencies = self.NewDependencies[mission]

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
        # Invert the map to show what each mission unlocks instead of dependencies
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
        self.SettingsInputs: Dict[str, str]  = {
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

    def RevertMissionsToDefaults(self) -> None:
        for mission in self.DefaultDependencies:
            bl2sdk.Log(f"{mission}: {self.DefaultDependencies[mission]}")
            bl2sdk.Log(f"{type(mission)}, {type(self.DefaultDependencies[mission])}")
            mission.Dependencies = self.DefaultDependencies[mission]

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

            # Save the default mission Dependencies, so that we're able to restore them
            self.DefaultDependencies: Dict[bl2sdk.UObject, bl2sdk.FArray] = {}
            for mission in bl2sdk.FindAll("MissionDefinition"):
                # Filter out the default MissionDefinition and all main missions
                if mission.bPlotCritical or not mission.MissionName:
                    continue

                bl2sdk.Log(f"{type(mission)}, {type(mission.Dependencies)}")
                self.DefaultDependencies[mission] = mission.Dependencies

            self.LoadFromFile()


        elif name == "Reload From File":
            self.LoadFromFile()

        elif name == "New Seed":
            SMRSeed = SideMissionRandomizerSeed(random.randrange(0xFFFFFFFF), "")
            self.SeedInfo.append(SMRSeed)
            self.SaveSeedInfo()

            newMod = SideMissionRandomizerChild(SMRSeed)

            index = bl2sdk.Mods.index(self) + 1
            bl2sdk.Mods.insert(index, newMod)

            self.EnableChild(newMod)

        elif name == "Delete All":
            if path.exists(self.SEED_PATH):
                os.remove(self.SEED_PATH)
            self.LoadFromFile()

        elif name == "Open Seed File":
            os.startfile(self.SEED_PATH)

    def LoadFromFile(self) -> None:
        # Clear out any existing mods in the list
        toRemove = set()
        for mod in bl2sdk.Mods:
            if isinstance(mod, SideMissionRandomizerChild):
                toRemove.add(mod)
        for mod in toRemove:
            bl2sdk.Mods.remove(mod)
        self.RevertMissionsToDefaults()
        self.CurrentlyEnabledChild = None

        # Create all of the child mods
        index = bl2sdk.Mods.index(self) + 1
        self.SeedInfo = self.LoadSeedInfo()
        for seed in self.SeedInfo:
            bl2sdk.Mods.insert(index, SideMissionRandomizerChild(seed))

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
        self.SaveSeedInfo()

SMRParent: SideMissionRandomizerParent = SideMissionRandomizerParent()
bl2sdk.Mods.append(SMRParent)
