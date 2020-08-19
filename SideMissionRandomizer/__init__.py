import unrealsdk
import json
import random
from dataclasses import dataclass
from os import path, remove, startfile
from typing import Dict, List, Optional, Tuple

from Mods.ModMenu import GetSettingsFilePath, Mods, ModTypes, SDKMod


# Simple data class to store the info we need about each seed
@dataclass
class SideMissionRandomizerSeed:
    Seed: int
    Name: str


# This class just store the base info about the mod in a single place
class SideMissionRandomizerBase(SDKMod):
    Name: str = "Side Mission Randomizer"
    Author: str = "apple1417"
    Description: str = (
        "Randomizes the progression order of side missions.\n"
    )
    Version: str = "1.4"

    Types: ModTypes = ModTypes.Gameplay


# This class defines each individual mod for each seed
class SideMissionRandomizerChild(SideMissionRandomizerBase):
    SettingsInputs: Dict[str, str] = {
        "Enter": "Enable",
        "Delete": "Delete",
        "D": "Dump Progression"
    }

    DUMP_PATH: str
    SMRSeed: SideMissionRandomizerSeed
    NewDependencies: Dict[unrealsdk.UObject, List[unrealsdk.UObject]]

    def __init__(self, SMRSeed: SideMissionRandomizerSeed) -> None:
        self.SMRSeed = SMRSeed

        # If you don't define a name just use the actual seed
        seed_name = self.SMRSeed.Name
        if len(seed_name) == 0:
            seed_name = str(self.SMRSeed.Seed)

        self.DUMP_PATH = path.join(path.dirname(GetSettingsFilePath(self)), f"{seed_name}.txt")
        self.Name += f" ({seed_name})"
        self.Description += f"\nSeed: {self.SMRSeed.Seed}"

        rand = random.Random(SMRSeed.Seed)

        def randSample(array: List[unrealsdk.UObject]) -> List[unrealsdk.UObject]:
            amount = min(10, len(array), max(1, int(rand.normalvariate(3, 2))))
            return rand.sample(array, amount)

        # To generate the random tree:
        #  1. Select a few missions to be unlocked by default
        #  2. Select a random mission that hasn't been unlocked yet
        #  3. Set it's dependencies to be a random selection of the unlocked missions
        #  4. Add it to the unlocked set and loop
        locked_missions = list(parent_instance.DefaultDependencies.keys())

        starting_amount = min(30, len(locked_missions), max(1, int(rand.normalvariate(20, 5))))
        availible_missions = rand.sample(locked_missions, starting_amount)

        self.NewDependencies: Dict[unrealsdk.UObject, List[unrealsdk.UObject]] = {}
        for m in availible_missions:
            locked_missions.remove(m)
            self.NewDependencies[m] = []

        while len(locked_missions) > 0:
            new_mission = rand.choice(locked_missions)
            locked_missions.remove(new_mission)

            self.NewDependencies[new_mission] = randSample(availible_missions)

            availible_missions.append(new_mission)

    def Enable(self) -> None:
        for mission in self.NewDependencies:
            mission.Dependencies = self.NewDependencies[mission]
            mission.ObjectiveDependency = (None, 0)

    def SettingsInputPressed(self, name: str) -> None:
        # Most of these pass through into the parent mod cause we only want to let one child be
        #  active at a time
        if name == "Enable":
            parent_instance.EnableChild(self)

        elif name == "Disable":
            parent_instance.DisableChild(self)

        elif name == "Delete":
            parent_instance.RemoveChild(self)

        elif name == "Dump Progression":
            self.DumpToFile()

    def DumpToFile(self) -> None:
        # Invert the map to show what each mission unlocks instead of dependencies
        # This is just a nicer sorting order
        unlock_map: Dict[str, List[str]] = {}
        defaults: List[str] = []
        for mission in self.NewDependencies:
            count = 0
            for dep in self.NewDependencies[mission]:
                if dep.MissionName in unlock_map:
                    unlock_map[dep.MissionName].append(mission.MissionName)
                else:
                    unlock_map[dep.MissionName] = [mission.MissionName]
                count += 1
            if count == 0:
                defaults.append(mission.MissionName)

        with open(self.DUMP_PATH, "w") as file:
            file.write(
                "# I recommend you put this into a dot file grapher such as http://www.webgraphviz.com/\n"
                "digraph G {\n\n"
            )
            for mission in sorted(defaults):
                file.write(f'"No Dependencies" -> "{mission}"\n')
            file.write("\n")
            for mission in sorted(unlock_map.keys()):
                for unlock in sorted(unlock_map[mission]):
                    file.write(f'"{mission}" -> "{unlock}"\n')
            file.write("\n}\n")

        startfile(self.DUMP_PATH)


# This class defines the single parent "Mod" that you use to create the child mods
class SideMissionRandomizerParent(SideMissionRandomizerBase):
    Description: str = (
        f"{SideMissionRandomizerBase.Description}"
        f"\n"
        f"Note that after loading this mod you still need to enable it on a particular seed."
    )
    Status: str = "<font color='#FF0000'>Not Loaded</font>"

    SettingsInputs: Dict[str, str] = {
        "Enter": "Load"
    }

    SEED_PATH: str
    SeedInfo: List[SideMissionRandomizerSeed]
    CurrentlyEnabledChild: Optional[SideMissionRandomizerChild]

    DefaultDependencies: Dict[unrealsdk.UObject, List[unrealsdk.UObject]]
    DefaultObjectiveDependencies: Dict[unrealsdk.UObject, Tuple[unrealsdk.UObject, int]]

    def __init__(self) -> None:
        self.SEED_PATH = path.join(path.dirname(GetSettingsFilePath(self)), "seeds.json")
        self.SeedInfo = []
        self.CurrentlyEnabledChild = None

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
            self.Status = "<font color='#00FF00'>Loaded</font>"

            # Save the default mission dependencies, so that we're able to restore them
            # We can't do this in __init__() cause they're not all loaded at that point
            self.DefaultDependencies = {}
            self.DefaultObjectiveDependencies = {}
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
            smr_seed = SideMissionRandomizerSeed(seed, str(seed))
            self.SeedInfo.append(smr_seed)
            self.SaveSeedInfo()

            new_mod = SideMissionRandomizerChild(smr_seed)
            Mods.append(new_mod)
            self.EnableChild(new_mod)

        elif name == "Delete All":
            if path.exists(self.SEED_PATH):
                remove(self.SEED_PATH)
            self.LoadFromFile()

        elif name == "Open Seed File":
            if not path.exists(self.SEED_PATH):
                self.SaveSeedInfo()
            startfile(self.SEED_PATH)

    def LoadFromFile(self) -> None:
        # Clear out any existing mods in the list
        to_remove = set()
        for mod in unrealsdk.Mods:
            if isinstance(mod, SideMissionRandomizerChild):
                to_remove.add(mod)
        for mod in to_remove:
            Mods.remove(mod)
        self.RevertMissionsToDefaults()
        self.CurrentlyEnabledChild = None

        # Create all of the child mods
        self.SeedInfo = self.LoadSeedInfo()
        for seed in self.SeedInfo:
            Mods.append(SideMissionRandomizerChild(seed))

    # Two helper functions to explicitly list the var names in the json dump
    def SaveSeedInfo(self) -> None:
        new_info = []
        for entry in self.SeedInfo:
            new_info.append({"Seed": entry.Seed, "Name": entry.Name})
        with open(self.SEED_PATH, "w") as file:
            json.dump(new_info, file, indent=2)

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


parent_instance: SideMissionRandomizerParent = SideMissionRandomizerParent()
Mods.append(parent_instance)
