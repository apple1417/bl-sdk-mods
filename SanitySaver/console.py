import unrealsdk
import argparse

try:
    from Mods import CommandExtensions
except ImportError:
    CommandExtensions = None  # type: ignore


def enable_console_commands() -> None:
    if CommandExtensions is None:
        return

    def dump_handler(args: argparse.Namespace) -> None:
        inv_manager = unrealsdk.GetEngine().GamePlayers[0].Actor.GetPawnInventoryManager()
        if inv_manager is None:
            unrealsdk.Log("Couldn't find inventory, are you in game?")
            return

        # By default dump all
        if not any((args.equipped, args.backpack, args.items, args.weapons)):
            args.equipped = True
            args.backpack = True
            args.items = True
            args.weapons = True

        seen = set()

        def log_item(item: unrealsdk.UObject) -> None:
            if item is None:
                return
            if not (args.items, args.weapons)[item.Class.Name == "WillowWeapon"]:
                return
            if item in seen:
                return
            seen.add(item)

            unique_id = item.DefinitionData.UniqueId
            name = item.GetShortHumanReadableName()

            unrealsdk.Log(f"{unique_id}: {name}")

        if args.equipped:
            for item in (inv_manager.ItemChain, inv_manager.InventoryChain):
                while item is not None:
                    log_item(item)
                    item = item.Inventory

            if inv_manager.Role < 3:
                log_item(inv_manager.BackpackInventoryBeingEquipped)

        if args.backpack:
            for item in inv_manager.Backpack:
                log_item(item)

            if inv_manager.Role < 3:
                log_item(inv_manager.EquippedInventoryGoingToBackpack)

    dump_parser = CommandExtensions.RegisterConsoleCommand(
        "SanitySaverDump",
        dump_handler,
        description=(
            "Dumps ids of all items and weapons on the current character, to aid in save editing."
            " By default, dumps all gear. You may use the optional arguments to narrow this down."
        )
    )
    dump_parser.add_argument(
        "-e", "--equipped",
        action="store_true",
        help="Dump equipped gear."
    )
    dump_parser.add_argument(
        "-b", "--backpack",
        action="store_true",
        help="Dump backpack gear."
    )
    dump_parser.add_argument(
        "-i", "--items",
        action="store_true",
        help="Dump items."
    )
    dump_parser.add_argument(
        "-w", "--weapons",
        action="store_true",
        help="Dump weapons."
    )


def disable_console_commands() -> None:
    if CommandExtensions is None:
        return

    CommandExtensions.UnregisterConsoleCommand("SanitySaverDump")
