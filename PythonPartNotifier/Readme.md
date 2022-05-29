# Python Part Notifier
Shows the parts making up all of your items and weapons on their cards - yes even including
Grenades, COMs, and Relics/Oz Kits.

# Adding names to custom parts as a Mod Author
When [Command Extensions](https://bl-sdk.github.io/mods/CommandExtensions/) is installed, this mod
registers a few new console commands you can use to add names to custom parts. Since CE ignores
unregisterd commands, using this won't cause any issues if someone has CE installed but not PPN.

## `set_part_name`
usage: `set_part_name [-h] [-g {BL2,TPS,AoDK} NAME] [-y] part name type slot`

Sets the name used for the given part. Note that this command is very sensitive to punctuation, best
to quote all args.

| positional arguments | |
|:---|:---|
| `part` | The part to set the name of. |
| `name` | The part's name, e.g. 'Bandit'. |
| `type` | The item type the part is intended for, e.g. 'Shotgun'. |
| `slot` | The slot the part is intended to go into, e.g. 'Stock'. |

| optional arguments: ||
|:---|:---|
| `-h, --help` | show this help message and exit |
| `-g {BL2,TPS,AoDK} NAME, --game-override {BL2,TPS,AoDK} NAME` | Set game-specific part name overrides. May be used multiple times. |
| `-y, --dry-run` | Don't modify anything, just print what the command would set the name to. Useful to check it's being parsed as expected. |

The `name`, `type`, and `slot` arguments may include both text and html-style markup -
`"[shock]Shock[-shock] <font color='#3c8eff'>Rare</font>"`.

## `get_part_name`
usage: `get_part_name [-h] part`

Gets the stored part name info for the given part.

| positional arguments | |
|:---|:---|
| `part` | The part to get the name of. |

| optional arguments: ||
|:---|:---|
| `-h, --help` | show this help message and exit |

## `delete_part_name`
usage: `delete_part_name [-h] part`

Deletes the stored part name info for the given part.

| positional arguments | |
|:---|:---|
| `part` | The part to delete the stored name of. |

| optional arguments: ||
|:---|:---|
| `-h, --help` | show this help message and exit |

# Changelog

### Python Part Notifier v1.9
- Renamed the `name_part` console command to `set_part_name`.
- Split out the `--delete` argument to it's own `delete_part_name` console command.
- Added the `get_part_name` console command.
- Allowed custom part names to use text markup tags (`[shock]Shock[-shock]`).
- Removed the overzealous automatic element/rarity colouring, and manually added it instead.

### Python Part Notifier v1.8
- Fixed that the settings menu included Oz Kits instead of Relics in AoDK.
- Started moving towards a hardcoded part name list - many more (typically unique) parts now have
  proper names
- Split the "Detailed Part Names" option into two, one for item type, one for slot.
- Added the `name_part` console command when Command Extensions is installed.
- Removed unicode replacements (save for a warning). The mod now relies on some ModMenu 2.4
  features, which should come with the correct sdk version anyway.

### Python Part Notifier v1.7
- Remove the unicode replacements when running on sdk version >=0.7.9, where it's fixed.

### Python Part Notifier v1.6
- Adds curly single and double quotes to the unicode replacements, fixing a few cases it broke in
  Exodus.

### Python Part Notifier v1.5
- Now provides a font size option, to make the parts text smaller to reduce the chance that
  information gets cut off.
- Fixed a case where the part headers would get coloured on certain items if gearbox forgot to add a
  closing tag somewhere.

### Python Part Notifier v1.4
- Updated to use some of the new features from SDK version 0.7.8. Most notably, the enabled state is
  now saved over game launches.

### Python Part Notifier v1.3
- Now opens a webpage listing requirements when you don't install them all.

### Python Part Notifier v1.2
- Updated to use OptionsWrapper - no functionality changes.

### Python Part Notifier v1.1
- Updated for SDK versions 0.7.4-0.7.6.
- The glitch weapon accessories should all now properly have their effect displayed.

### Python Part Notifier v1.0
- Inital Release.
