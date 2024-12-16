from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import TYPE_CHECKING

import unrealsdk
from mods_base import command
from unrealsdk import logging

from . import obj_name_splitter, parse_object

if TYPE_CHECKING:
    import argparse

    from unrealsdk.unreal import UClass, UObject, WrappedStruct


@dataclass(frozen=True)
class BVCTuple:
    BaseValueConstant: float
    BaseValueAttribute: UObject | None
    InitializationDefinition: UObject | None
    BaseValueScaleConstant: float

    def as_struct(self) -> WrappedStruct:
        """
        Coverts this to a wrapped struct.

        Returns:
            The wrapped struct equivalent.
        """
        return unrealsdk.make_struct(
            "AttributeInitializationData",
            BaseValueConstant=self.BaseValueConstant,
            BaseValueAttribute=self.BaseValueAttribute,
            InitializationDefinition=self.InitializationDefinition,
            BaseValueScaleConstant=self.BaseValueScaleConstant,
        )


@dataclass(frozen=True)
class ManufacturerDataProxy:
    Manufacturer: UObject | None
    # Storing the BVC tuple directly, rather than the index
    DefaultWeight: BVCTuple

    def as_struct(self, caid: list[BVCTuple]) -> WrappedStruct:
        """
        Coverts this to a wrapped struct.

        Args:
            caid: The caid list to index into.
        Returns:
            The wrapped struct equivalent.
        """
        return unrealsdk.make_struct(
            "ManufacturerCustomGradeWeightData",
            Manufacturer=self.Manufacturer,
            DefaultWeightIndex=caid.index(self.DefaultWeight),
        )


@dataclass(frozen=True)
class WeightedPartProxy:
    Part: UObject | None
    Manufacturers: list[ManufacturerDataProxy]
    # Storing the BVC tuples directly again, rather than the indexes
    MinGameStageIndex: BVCTuple
    MaxGameStageIndex: BVCTuple
    DefaultWeightIndex: BVCTuple

    def as_struct(self, caid: list[BVCTuple]) -> WrappedStruct:
        """
        Coverts this to a wrapped struct.

        Args:
            caid: The caid list to index into.
        Returns:
            The wrapped struct equivalent.
        """
        return unrealsdk.make_struct(
            "PartGradeWeightData",
            Part=self.Part,
            Manufacturers=[m.as_struct(caid) for m in self.Manufacturers],
            MinGameStageIndex=caid.index(self.MinGameStageIndex),
            MaxGameStageIndex=caid.index(self.MaxGameStageIndex),
            DefaultWeightIndex=caid.index(self.DefaultWeightIndex),
        )


"""
Gearbox are masters of inconsistency, so despite doing the exact same thing, the item and weapon
 classes don't inherit from each other, and use different field names all over the place.
It's a miracle that the weighted parts lists (which are completely different structs) use the exact
 same field names and order so we don't need to do this for them.

All these tuples are organised with the item version at index 0 and weapon version at index 1.
"""
BALANCE_CLASSES: tuple[UClass, UClass] = (
    unrealsdk.find_class("ItemBalanceDefinition"),
    unrealsdk.find_class("WeaponBalanceDefinition"),
)
BASE_LIST_FIELD: tuple[str, str] = ("ItemPartListCollection", "WeaponPartListCollection")

LIST_SLOTS: tuple[tuple[str, ...], tuple[str, ...]] = (
    (
        "AlphaPartData",
        "BetaPartData",
        "GammaPartData",
        "DeltaPartData",
        "EpsilonPartData",
        "ZetaPartData",
        "EtaPartData",
        "ThetaPartData",
        "MaterialPartData",
    ),
    (
        "BodyPartData",
        "GripPartData",
        "BarrelPartData",
        "SightPartData",
        "StockPartData",
        "ElementalPartData",
        "Accessory1PartData",
        "Accessory2PartData",
        "MaterialPartData",
    ),
)


class ItemType(IntEnum):
    ITEM = 0
    WEAPON = 1

    @staticmethod
    def detect(obj: UObject) -> ItemType | None:
        """
        Detect what type the given object is.

        Args:
            obj: The object to detect item type of.
        Returns:
            The item type, or None on error.
        """
        is_weapon = obj.Class._inherits(BALANCE_CLASSES[ItemType.WEAPON])
        is_item = obj.Class._inherits(BALANCE_CLASSES[ItemType.ITEM])

        match is_weapon, is_item:
            case True, False:
                return ItemType.WEAPON
            case False, True:
                return ItemType.ITEM
            case _, _:
                logging.error(
                    f"Object {obj} must be a '{BALANCE_CLASSES[ItemType.WEAPON]}' or"
                    f" '{BALANCE_CLASSES[ItemType.ITEM]}'!",
                )
                return None


def get_caid(parts_list: UObject, index: int) -> BVCTuple:
    """
    Reads a value out of the CAID on a parts list.

    Args:
        parts_list: The parts list to look at the CAID on.
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


def gather_parts_lists(
    final_bal: UObject,
    item_type: ItemType,
) -> dict[str, list[WeightedPartProxy]] | None:
    """
    Given a balance, work out what it's final parts list should be.

    Args:
        final_bal: The balance to gather tha parts lists of.
        item_type: What item type this balance is.
    Returns:
        A parts list dict, or None on error.
    """

    # Since the later balances overwrite earlier ones, put them into a stack
    balance_stack: list[UObject] = []
    bal = final_bal
    while bal is not None:
        if not bal.Class._inherits(BALANCE_CLASSES[item_type]):
            logging.error(
                f"Base balance '{bal.PathName(bal)}' is of a different class than the final balance"
                f" being edited. Unsure how to handle this, quitting.",
            )
            return None

        balance_stack.append(bal)
        bal = bal.BaseDefinition

    # Find what the runtime parts list should use
    parts: dict[str, list[WeightedPartProxy]] = {}
    while balance_stack:
        bal = balance_stack.pop()
        parts_list = getattr(bal, BASE_LIST_FIELD[item_type])
        if parts_list is None:
            logging.error(f"Base balance '{bal.PathName(bal)}' does not contain a parts list!")
            return None

        for slot in LIST_SLOTS[item_type]:
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
                            get_caid(parts_list, m.DefaultWeightIndex),
                        )
                        for m in entry.Manufacturers
                    ],
                    get_caid(parts_list, entry.MinGameStageIndex),
                    get_caid(parts_list, entry.MaxGameStageIndex),
                    get_caid(parts_list, entry.DefaultWeightIndex),
                )
                for entry in part_data.WeightedParts
            ]

    return parts


def gather_required_caid(parts: dict[str, list[WeightedPartProxy]]) -> list[BVCTuple]:
    """
    Gathers all tuples that need to be placed into the CAID for the given parts.

    Args:
        parts: The parts dict.
    Returns:
        A list of required caid entries.
    """

    caid: set[BVCTuple] = set()
    for weighted_parts in parts.values():
        for entry in weighted_parts:
            for manu in entry.Manufacturers:
                caid.add(manu.DefaultWeight)
            caid.add(entry.MinGameStageIndex)
            caid.add(entry.MaxGameStageIndex)
            caid.add(entry.DefaultWeightIndex)
    return sorted(caid, key=lambda b: b.BaseValueConstant)  # type: ignore


@command(
    splitter=obj_name_splitter,
    description=(
        "Regenerates the runtime parts list of an item/weapon balance, to reflect changes in the"
        " base part lists."
        " Edits objects in place."
    ),
)
def regen_balance(args: argparse.Namespace) -> None:  # noqa: D103
    final_bal = parse_object(args.balance)
    if final_bal is None:
        return

    if (item_type := ItemType.detect(final_bal)) is None:
        return

    runtime_parts_list = final_bal.RuntimePartListCollection
    if runtime_parts_list is None:
        logging.error("Balance does not contain a runtime parts list!")
        return

    if (parts := gather_parts_lists(final_bal, item_type)) is None:
        return

    caid = gather_required_caid(parts)
    runtime_parts_list.ConsolidatedAttributeInitData = [x.as_struct() for x in caid]

    for slot in LIST_SLOTS[item_type]:
        part_type_data = getattr(runtime_parts_list, slot)
        # If a slot's not defined, make sure to set it as not enabled
        if slot not in parts:
            part_type_data.bEnabled = False
            part_type_data.WeightedParts = []
            continue

        part_type_data.bEnabled = True
        part_type_data.WeightedParts = [x.as_struct(caid) for x in parts[slot]]


regen_balance.add_argument("balance", help="The balance to regenerate.")
