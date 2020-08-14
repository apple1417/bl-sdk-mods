import unrealsdk
import math as maths
import random
from enum import Enum
from typing import ClassVar, Optional, Tuple

from . import JSON, QueuedCrowdControlEffect
from Mods import AsyncUtil
from Mods.UserFeedback import ShowHUDMessage

Location = Tuple[float, float, float]
Rotation = Tuple[int, int, int]

PLAYER_ALLEGIANCE = "PawnAllegiance GD_AI_Allegiance.Allegiance_Player"


class Direction(Enum):
    F = 0
    FL = maths.pi / 4
    L = maths.pi / 2
    BL = 3 * maths.pi / 4
    B = maths.pi
    BR = 5 * maths.pi / 4
    R = 3 * maths.pi / 2
    FR = 7 * maths.pi / 4


def PickRandomBalance() -> Optional[unrealsdk.UObject]:
    filtered = []
    for bal in unrealsdk.FindAll("AIPawnBalanceDefinition"):
        if bal.AIPawnArchetype is None:
            continue
        alleg = bal.AIPawnArchetype.Allegiance
        if str(alleg) == PLAYER_ALLEGIANCE:
            continue

        # OPINION_Enemy = 0
        should_append = alleg.DefaultOpinion == 0
        for op in alleg.MyOpinions:
            if str(op.Allegiance) == PLAYER_ALLEGIANCE:
                should_append = op.Opinion == 0
                break
        if should_append:
            filtered.append(bal)
    if len(filtered) == 0:
        return None
    return random.choice(filtered)


def SpawnEnemyAt(balDef: unrealsdk.UObject, level: int, pos: Location, rot: Rotation) -> Optional[unrealsdk.UObject]:
    pawn = balDef.AIPawnArchetype
    spawned = unrealsdk.FindAll("WillowPopulationMaster")[-1].SpawnPopulationControlledActor(
        pawn.Class,
        None,
        "None",
        pos,
        rot,
        pawn,
        False,
        False
    )
    if spawned is None:
        return None

    # This does most of what PopulationFactoryBalancedAIPawn.SetupBalancedPopulationActor() does
    # It might miss some critical stuff but it works for this
    spawned.SetGameStage(level)
    spawned.SetExpLevel(level)
    spawned.SetGameStageForSpawnedInventory(level)
    spawned.SetAwesomeLevel(0)

    spawned.Controller.InitializeCharacterClass()
    spawned.Controller.RecalculateAttributeInitializedState()

    spawned.InitializeBalanceDefinitionState(balDef, -1)
    balDef.SetupPawnItemPoolList(spawned)
    spawned.AddDefaultInventory()

    return spawned


class SpawnEnemy(QueuedCrowdControlEffect):
    Name: ClassVar[str] = "Spawn Enemy"
    Description: ClassVar[str] = (
        "Picks a random enemy type available in the world and spawns a higher level version in"
        " front of you.\n"
        "The enemy's AI may be wonky at times."
    )

    Interval: ClassVar[int] = 15

    Distance: ClassVar[float] = 1000
    LevelOffset: ClassVar[int] = 4

    def OnRun(self, msg: JSON) -> None:
        bal_def = PickRandomBalance()
        if bal_def is None:
            self.ShowFailedMessage(msg)
            return

        self.ShowRedemption(msg)

        PC = unrealsdk.GetEngine().GamePlayers[0].Actor
        level = PC.Pawn.GetGameStage() + PC.PlayerReplicationInfo.NumOverpowerLevelsUnlocked
        pos, rot = self.TranslatePos(PC.Pawn.Location, PC.Rotation, Direction.F)

        SpawnEnemyAt(bal_def, level + self.LevelOffset, pos, rot)

    def ShowFailedMessage(self, msg: JSON) -> None:
        def Internal() -> None:
            user = "Unknown user"
            try:
                user = msg["data"]["redemption"]["user"]["login"]
            except KeyError:
                pass
            ShowHUDMessage(
                "Crowd Control",
                f"{user} tried to redeem '{self.Name}', but forgot that this world doesn't have any enemies."
            )
        # There's a small delay after closing menus before we can properly show a message
        AsyncUtil.RunIn(0.1, Internal)

    def TranslatePos(self, pos: unrealsdk.FStruct, rot: unrealsdk.FStruct, dir: Direction) -> Tuple[Location, Rotation]:
        conversion = maths.pi / 0x7fff
        x_offset = maths.cos(rot.Yaw * conversion - dir.value) * self.Distance
        y_offset = maths.sin(rot.Yaw * conversion - dir.value) * self.Distance
        yaw_offset = int(dir.value / conversion)
        return ((
            pos.X + x_offset,
            pos.Y + y_offset,
            pos.Z
        ), (
            0,
            rot.Yaw + yaw_offset,
            0
        ))


class SpawnHorde(SpawnEnemy):
    Name: ClassVar[str] = "Spawn Horde"
    Description: ClassVar[str] = (
        "Picks a random enemy type available in the world and spawns a horde of them around each"
        " player.\n"
        "The enemies' AI may be wonky at times."
    )

    Distance: ClassVar[float] = 1500
    LevelOffset: ClassVar[int] = 1

    def OnRun(self, msg: JSON) -> None:
        if PickRandomBalance() is None:
            self.ShowFailedMessage(msg)
            return

        self.ShowRedemption(msg)

        for PC in unrealsdk.FindAll("WillowPlayerController"):
            if PC.Name.startswith("Default__"):
                continue

            bal_def = PickRandomBalance()
            level = PC.Pawn.GetGameStage() + PC.PlayerReplicationInfo.NumOverpowerLevelsUnlocked

            for dir in Direction:
                pos, rot = self.TranslatePos(PC.Pawn.Location, PC.Rotation, dir)
                SpawnEnemyAt(bal_def, level + self.LevelOffset, pos, rot)
