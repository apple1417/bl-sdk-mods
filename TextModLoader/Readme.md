# Text Mod Loader
Displays Text Mods from binaries in the SDK mods menu.

# Customizing the description as a Mod Author
Text Mod Loader extracts BLIMP tags, from mod files and uses them to customize how the it displays.
You can read the [full BLIMP spec here](https://github.com/apple1417/blcmm-parsing/tree/master/blimp),
but to summarize, simply add a few tags to the first comment block at the top of the file.

```
@title My Mod
@author apple1417 
@version 1.1
@description Does moddy things.
```

Text Mod Loader supports the following tags.

Tag Name |  Multiple | Intepretation
:---|:---:|:---
`@author` | Allowed | The mod's author(s), all joined into a list, replacing `TextModLoader`.
`@description` | Allowed | Joined in the order encountered to create the mod's description. A tag with an empty value (after stripping whitespace) joins surrounding values with a newline, all other pairs are joined using a space.
`@main-author` | First | Used as the mod's "main author", placed at the start of the author list.
`@title` | First | The mod's title, replacing the filename.
`@version` | First | The mod's version. Entirely visual, can be any arbitrary string.
---|---|---
`@tml-priority` | First | Sets the priority for the mod menu entry, takes an integer. Use 0 to have the same as priority as standard SDK mods.
`@tml-ignore-me` | n/a | If any instance of this tag exists, prevents the mod from being listed in the mods menu. Value is ignored.

# Writing SDK-text mod hybrids
You can use Text Mod Loader as a base for a hybrid SDK mod which executes text mods, allowing you to
make use of all it's features. In particular, BLIMP tags will automatically be parsed, so you don't
need to duplicate their contents, and all the mod locking logic will continue running so people
can't overwrite your hotfixes with another mod's.

To add your own text mods, call `add_custom_mod_path` (requires >=v1.4). This adds to the locations
Text Mod Loader checks when loading mods - make sure to call it before getting to the main menu. 

If all you want to do is make some files show up in the Mods menu, simply call it with their paths.
```py
from os import path

try:
    from Mods import TextModLoader
    if TextModLoader.VERSION < (1, 4):
        raise ImportError("MyCoolMod requires at least TextModLoader v1.4", f"Have: {TextModLoader.VERSION}")
except ImportError as ex:
    import webbrowser
    url = "https://bl-sdk.github.io/requirements/?mod=My%20Cool%20Mod&all"
    if len(ex.args) > 1:
        url += "&update"
    webbrowser.open("https://bl-sdk.github.io/requirements/?mod=My%20Cool%20Mod&all&update")
    raise ex

from Mods.TextModLoader import add_custom_mod_path

add_custom_mod_path(path.join(path.dirname(__file__), "my_cool_mod.blcm"))
```

Most of the time however, you'll want to run some custom logic when it's enabled. To do this,
subclass `TextMod`, override `Enable`, and provide your new class as an extra argument.
```py
class Sanic(TextMod):
    def Enable(self) -> None:
        super().Enable()
        unrealsdk.Log("Gotta go fast")

add_custom_mod_path(path.join(path.dirname(__file__), "sanic.blcm"), Sanic)
```

# Changelog

## Text Mod Loader v1.4
- Added `add_custom_mod_path`, and made a few other internal changes to allow other SDK mods to use
  this as a base.

## Text Mod Loader v1.3
- Updated the file parsing with a few new tweaks we made to BLIMP tags.

## Text Mod Loader v1.2
- Updated the file parsing to better handle non-ascii text. The handling is still not perfect, but
  should cover most cases.

## Text Mod Loader v1.1
- Fixed recommended game detection - you'll now get a warning when trying to run a mod file in a
  game it's not intended for.
- Fixed that editing a mod would cause it to stop being auto-enabled.
- Forced all mod info to be reloaded whenever you update TML.

## Text Mod Loader v1.0
- Inital Release.
