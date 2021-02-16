import unrealsdk
import argparse
import functools
from typing import Callable, Dict

from .. import RegisterConsoleCommand
from . import obj_name_splitter, parse_object
from .clone import clone_object, parse_clone_target

"""
We pass a known clones dict between functions so that we don't clone the same object twice (if it's
stored in two different locations)
"""
ClonesDict = Dict[unrealsdk.UObject, unrealsdk.UObject]


# There are a bunch of different fields skills can be stored in, hence the field arg
def fixup_skill_field(field: str, behavior: unrealsdk.UObject, known_clones: ClonesDict) -> None:
    skill = getattr(behavior, field)
    if skill is None:
        return

    if skill in known_clones:
        setattr(behavior, field, known_clones[skill])
        return

    cloned_skill = clone_object(
        skill,
        behavior,
        # Empty string gives us the auto numbering back
        "" if skill.Name == skill.Class.Name else skill.Name
    )
    if cloned_skill is None:
        return
    known_clones[skill] = cloned_skill

    setattr(behavior, field, cloned_skill)

    bpd = cloned_skill.BehaviorProviderDefinition
    if bpd is None:
        return

    if bpd in known_clones:
        cloned_skill.BehaviorProviderDefinition = known_clones[bpd]
        return

    cloned_bpd = clone_object(
        bpd,
        cloned_skill,
        "" if bpd.Name == bpd.Class.Name else bpd.Name
    )
    if cloned_bpd is None:
        return
    known_clones[bpd] = cloned_bpd

    cloned_skill.BehaviorProviderDefinition = cloned_bpd
    fixup_bpd(cloned_bpd, known_clones)


# Mapping behavior class names to functions that perform extra fixup on them
extra_behaviour_fixups: Dict[str, Callable[[unrealsdk.UObject, ClonesDict], None]] = {
    "Behavior_AttributeEffect": functools.partial(fixup_skill_field, "AttributeEffect"),
    "Behavior_ActivateSkill": functools.partial(fixup_skill_field, "SkillToActivate"),
    "Behavior_DeactivateSkill": functools.partial(fixup_skill_field, "SkillToDeactivate"),
}


def fixup_bpd(cloned: unrealsdk.UObject, known_clones: ClonesDict) -> None:
    for sequence in cloned.BehaviorSequences:
        # There are a bunch of other fields, but this seems to be the only used one
        for data in sequence.BehaviorData2:
            behavior = data.Behavior
            if behavior is None:
                continue

            if behavior in known_clones:
                data.Behavior = known_clones[behavior]
                continue

            cloned_behavior = clone_object(
                behavior,
                cloned,
                "" if behavior.Name == behavior.Class.Name else behavior.Name
            )
            if cloned_behavior is None:
                continue
            known_clones[behavior] = cloned_behavior

            data.Behavior = cloned_behavior

            extra_fixup = extra_behaviour_fixups.get(cloned_behavior.Class.Name, None)
            if extra_fixup is not None:
                extra_fixup(cloned_behavior, known_clones)


def handler(args: argparse.Namespace) -> None:
    src = parse_object(args.base)
    if src is None:
        return
    if src.Class.Name != "BehaviorProviderDefinition":
        unrealsdk.Log(f"Object {src.PathName(src)} must be a 'BehaviorProviderDefinition'!")
        return

    outer, name = parse_clone_target(args.clone, src.Class.Name)
    if name is None:
        return

    cloned = clone_object(src, outer, name)
    if cloned is None:
        return
    fixup_bpd(cloned, {})


parser = RegisterConsoleCommand(
    "clone_bpd",
    handler,
    splitter=obj_name_splitter,
    description=(
        "Creates a clone of a BehaviourProvidierDefinition, as well as recursively cloning some of"
        " the objects making it up. This may not match the exact layout of the original objects,"
        " dump them manually to check what their new names are."
    )
)
parser.add_argument("base", help="The bpd to create a copy of.")
parser.add_argument("clone", help="The name of the clone to create.")
