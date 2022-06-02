import unrealsdk
import argparse
from dataclasses import dataclass
from typing import ClassVar, Dict, List, Set, Tuple

from .. import RegisterConsoleCommand
from . import is_obj_instance, obj_name_splitter, parse_object


@dataclass(frozen=True)
class BVCTuple:
    BaseValueConstant: float
    BaseValueAttribute: unrealsdk.UObject
    InitializationDefinition: unrealsdk.UObject
    BaseValueScaleConstant: float

    TupleType: ClassVar = Tuple[float, unrealsdk.UObject, unrealsdk.UObject, float]

    def as_tuple(self) -> TupleType:
        return (
            self.BaseValueConstant,
            self.BaseValueAttribute,
            self.InitializationDefinition,
            self.BaseValueScaleConstant,
        )


@dataclass(frozen=True)
class ManufacturerDataProxy:
    Manufacturer: unrealsdk.UObject
    # Storing the BVC tuple directly, rather than the index
    DefaultWeight: BVCTuple


@dataclass(frozen=True)
class WeightedPartProxy:
    Part: unrealsdk.UObject
    Manufacturers: List[ManufacturerDataProxy]
    # Storing the BVC tuples directly again, rather than the indexes
    MinGameStageIndex: BVCTuple
    MaxGameStageIndex: BVCTuple
    DefaultWeightIndex: BVCTuple


"""
Gearbox are masters of inconsistency, so despite doing the exact same thing, the item and weapon
 classes don't inherit from each other, and use different field names all over the place.
It's a miracle that the weighted parts lists (which are completely different structs) use the exact
 same field names and order so we don't need to do this for them.

All these tuples are organised with the item version at index 0 and weapon version at index 1.
"""
BALANCE_CLASSES: Tuple[str, str] = ("ItemBalanceDefinition", "WeaponBalanceDefinition")
BASE_LIST_FIELD: Tuple[str, str] = ("ItemPartListCollection", "WeaponPartListCollection")

LIST_SLOTS: Tuple[Tuple[str, ...], Tuple[str, ...]] = ((
    "AlphaPartData",
    "BetaPartData",
    "GammaPartData",
    "DeltaPartData",
    "EpsilonPartData",
    "ZetaPartData",
    "EtaPartData",
    "ThetaPartData",
    "MaterialPartData",
), (
    "BodyPartData",
    "GripPartData",
    "BarrelPartData",
    "SightPartData",
    "StockPartData",
    "ElementalPartData",
    "Accessory1PartData",
    "Accessory2PartData",
    "MaterialPartData",
))


def get_caid(parts_list: unrealsdk.UObject, index: int) -> BVCTuple:
    """
    Reads a value out of the CAID on a parts list.

    Args:
        list: The parts list to look at the CAID on.
        index: The index to look into.
    Returns:
        The CAID data, formatted into a BVC tuple ready for re-assignment.
    """
    bvc = parts_list.ConsolidatedAttributeInitData[index]
    return BVCTuple(
        bvc.BaseValueConstant,
        bvc.BaseValueAttribute,
        bvc.InitializationDefinition,
        bvc.BaseValueScaleConstant,
    )


def handler(args: argparse.Namespace) -> None:
    final_bal = parse_object(args.balance)
    if final_bal is None:
        return

    is_weap = is_obj_instance(final_bal, BALANCE_CLASSES[True])
    if not is_weap and not is_obj_instance(final_bal, BALANCE_CLASSES[False]):
        unrealsdk.Log(
            f"Object '{final_bal.PathName(final_bal)}' must be a '{BALANCE_CLASSES[True]}' or"
            f" '{BALANCE_CLASSES[False]}'!"
        )
        return

    runtime_parts_list = final_bal.RuntimePartListCollection
    if runtime_parts_list is None:
        unrealsdk.Log("Balance does not contain a runtime parts list!")
        return

    # Since the later balances overwrite earlier ones, put them into a stack
    balance_stack = []
    bal = final_bal
    while bal is not None:
        if not is_obj_instance(bal, BALANCE_CLASSES[is_weap]):
            unrealsdk.Log(
                f"Base balance '{bal.PathName(bal)}' is of a different class than the final balance"
                f" being edited. Unsure how to handle this, quitting."
            )
            return

        balance_stack.append(bal)
        bal = bal.BaseDefinition

    # Find what the runtime parts list should use
    parts: Dict[str, List[WeightedPartProxy]] = {}
    while balance_stack:
        bal = balance_stack.pop()
        parts_list = getattr(bal, BASE_LIST_FIELD[is_weap])
        if parts_list is None:
            unrealsdk.Log(f"Base balance '{bal.PathName(bal)}' does not contain a parts list!")
            return

        for slot in LIST_SLOTS[is_weap]:
            part_data = getattr(parts_list, slot)

            # If the slot isn't enabled, keep what's stored before
            if not part_data.bEnabled:
                continue

            # Parse from the standard struct into our proxy, where we store caid values directly
            parts[slot] = [
                WeightedPartProxy(
                    entry.Part,
                    [
                        ManufacturerDataProxy(
                            m.Manufacturer,
                            get_caid(parts_list, m.DefaultWeightIndex)
                        )
                        for m in entry.Manufacturers
                    ],
                    get_caid(parts_list, entry.MinGameStageIndex),
                    get_caid(parts_list, entry.MaxGameStageIndex),
                    get_caid(parts_list, entry.DefaultWeightIndex),
                )
                for entry in part_data.WeightedParts
            ]

    # Work out what caid we actually need
    caid: Set[BVCTuple.TupleType] = set()
    for weighted_parts in parts.values():
        for entry in weighted_parts:
            for manu in entry.Manufacturers:
                caid.add(manu.DefaultWeight)
            caid.add(entry.MinGameStageIndex)
            caid.add(entry.MaxGameStageIndex)
            caid.add(entry.DefaultWeightIndex)
    ordered_caid = sorted(caid, key=lambda b: b.BaseValueConstant)  # type: ignore

    # Set all the values on the runtime list
    runtime_parts_list.ConsolidatedAttributeInitData = [b.as_tuple() for b in ordered_caid]

    for slot in LIST_SLOTS[is_weap]:
        # If a slot's not defined, make sure to set it as not enabled
        if slot not in parts:
            setattr(runtime_parts_list, slot, (False, []))
            continue

        # Convert our nice data structures back into the tuple'd mess we need to set stuff with
        setattr(
            runtime_parts_list,
            slot,
            (
                True,
                [
                    (
                        entry.Part,
                        [
                            (
                                m.Manufacturer,
                                ordered_caid.index(m.DefaultWeight)
                            )
                            for m in entry.Manufacturers
                        ],
                        ordered_caid.index(entry.MinGameStageIndex),
                        ordered_caid.index(entry.MaxGameStageIndex),
                        ordered_caid.index(entry.DefaultWeightIndex),
                    )
                    for entry in parts[slot]
                ]
            )
        )


parser = RegisterConsoleCommand(
    "regen_balance",
    handler,
    splitter=obj_name_splitter,
    description=(
        "Regenerates the runtime parts list of an item/weapon balance, to reflect changes in the"
        " base part lists."
        " Edits objects in place."
    )
)
parser.add_argument("balance", help="The balance to regenerate.")
