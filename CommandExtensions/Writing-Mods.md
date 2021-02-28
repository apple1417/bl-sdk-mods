# Table of Contents
- [Table of Contents](#table-of-contents)
- [Built-in Custom Commands](#built-in-custom-commands)
  - [`CE_Debug`](#ce_debug)
  - [`clone`](#clone)
  - [`clone_bpd`](#clone_bpd)
  - [`load_package`](#load_package)
  - [`keep_alive`](#keep_alive)
  - [`set_early`](#set_early)
  - [`set_material`](#set_material)
  - [`suppress_next_chat`](#suppress_next_chat)
- [Writing Text Mods](#writing-text-mods)
  - [Parsing Intricacies](#parsing-intricacies)
    - [`CE_EnableOn`](#ce_enableon)
- [Adding new commands in your own SDK Mods](#adding-new-commands-in-your-own-sdk-mods)

# Built-in Custom Commands

## `CE_Debug`
usage: `CE_Debug [-h] {Enable,Disable}`

Enables/disables Command Extension debug logging. This logs a copy of each command to be run, useful
for checking that your blcm files are being handled correctly.

| positional arguments: | |
|:---|:---|
| `{Enable,Disable}` | |

| optional arguments | |
|:---|:---|
| `-h, --help` | show this help message and exit |


## `clone`
usage: `clone [-h] base clone`

Creates a clone of an existing object.

| positional arguments | |
|:---|:---|
| `base`  | The object to create a copy of. |
| `clone` | The name of the clone to create. |

| optional arguments | |
|:---|:---|
| `-h, --help` | show this help message and exit |

## `clone_bpd`
usage: `clone [-h] base clone`

Creates a clone of a BehaviourProvidierDefinition, as well as recursively cloning some of the
objects making it up. This may not match the exact layout of the original objects, dump them
manually to check what their new names are.

| positional arguments | |
|:---|:---|
| `base`  | The bpd to create a copy of. |
| `clone` | The name of the clone to create. |

| optional arguments | |
|:---|:---|
| `-h, --help` | show this help message and exit |

## `load_package`
usage: `load_package [-h] package`

Loads a package and all objects contained within it. This freezes the game as it loads; it should be
used sparingly. Supports using glob-style wildcards to load up to 10 packages at once, though being
explicit should still be prefered.

| positional arguments | |
|:---|:---|
| `package` | The package(s) to load. This uses the full upk names; not the shortened version hotfixes use. |

| optional arguments | |
|:---|:---|
| `-h, --help` | show this help message and exit |

## `keep_alive`
usage: `keep_alive [-h] object`

Prevents an object from being garbaged collected, it will always be loaded until you restart the
game.

| positional arguments | |
|:---|:---|
| `object` | The object to keep alive. |

| optional arguments | |
|:---|:---|
| `-h, --help` | show this help message and exit |

## `set_early`
usage: `set_early [-h] args [args ...]`

Behaves exactly like a set command. Only useful in files, as it's run during custom command parsing
instead of afterwards.

| positional arguments | |
|:---|:---|
| args | Standard set command arguments |

| optional arguments | |
|:---|:---|
| `-h, --help` | show this help message and exit |

## `set_material`
usage: `set_material [-h] part material`

Sets a parts's material, without causing crashes if it's a cloned from an existing one. Note that
cloning `Engine.Default__MaterialInstanceConstant` will not cause crashes, this command is most
useful when only making a small edit. Practically, this creates a new material and copies the fields
from the provided one as a template.

| positional arguments | |
|:---|:---|
| part     | The part to set the material on. |
| material | The MaterialInstanceConstant to set. |

| optional arguments | |
|:---|:---|
| `-h, --help` | show this help message and exit |

## `suppress_next_chat`
usage: `suppress_next_chat [-h] [pattern]`

Prevents the next chat message that matches a given glob pattern from being printed.  Multiple calls
to this stack, and suppress multiple messages.

This is intended to be used to suppress an error message, so that it only gets printed when someone
tries to `exec` your file without running Command Extensions.

| positional arguments | |
|:---|:---|
| `pattern` | The glob pattern matching the message to suppress. |

| optional arguments | |
|:---|:---|
| `-h, --help` | show this help message and exit |


# Writing Text Mods
You can automatically use all of these commands inside text mods exactly the same as in console.
Just add them inside BLCMM as comments, the mod automatically picks up `exec` commands and parses
through the files to execute whatever custom commands are stored in them. You can check out
[sanic.blcm](sanic.blcm) as an example.

## Parsing Intricacies
There are a few intricacies to how exactly mod files get parsed, which you might be interested in.

The first thing to realize is that all custom commands are run before any regular ones stored in the
file. When you run an `exec` command, the mod looks through the file, runs any custom commands in
it, and then lets the game handle the file normally. This is unlikely to have an impact, but is
worth noting.

If you `exec` a file that's *not* a BLCMM file, the mod falls back to a naive line-by-line approach.
For each line in the file, if that line matches a custom command, it runs that command.

BLCMM files use a bit more involved parsing. Custom commands can be enabled and disabled by toggling
the category they're in. This requires a bit a workaround however, which might cause some
interesting behaviour. BLCMM unfortuantly only stores if individual set commands enabled. Our custom
commands are technically comments, so they don't get this, and categories themselves don't have a
specific enabled state either. Instead, we have to determine if a custom command is enabled by if
the regular set commands around it are.

By default, a custom command is considered to be enabled if any regular command in the same category
as it also is. This only applies to the current category, it doesn't recurse down into subcategories
or up into parent ones. The state of subcategories also has no effect, only commands on the exact
same level do. In practice, most users will only enable/disable entire categories at a time, so as
long as you put custom commands in the same category as the normal commands that interact with them,
they should all get executed together.

There is actually one more built in command not mentioned before, which adjusts how exactly the
parser decides if a custom command is enabled or not. This command only works inside BLCMM files,
trying to run it from console or from a regular text file will result in an error.

### `CE_EnableOn`
usage: `CE_EnableOn [-h] {All,Any,Force,Next}`

Can only be used in BLCMM files.

Changes the strategy used to determine if custom command is enabled or not. Defaults to 'Any'.
This change applies until the end of the category, or until the next instance of this command.

Using each strategy, a custom command is enabled if:

| | |
|:---|:---|
| All   | All regular commands in the same category are enabled. |
| Any   | Any regular command in the same category is enabled. |
| Force | It is always enabled. |
| Next  | The next regular command after it (in the same category) is enabled. |

| positional arguments | |
|:---|:---|
| `{All,Any,Force,Next}` | |


| optional arguments | |
|:---|:---|
| `-h, --help` | show this help message and exit


# Adding new commands in your own SDK Mods
Command Extensions exports two functions: `RegisterConsoleCommand`, and `UnregisterConsoleCommand`.
Unsuprisingly, these are used to register and unregister console commands respectively. For the
exact arguments, check the docstrings. All command parsing is done through Python's standard
`argparse` library, the register function does a bit of basic setup before returning a
`ArgumentParser` instance (or rather, a small wrapper around it). You just need to add your
arguments to this object, everything else will automatically be handled for you. When your mod is
disabled you can unregister your commands to stop them from being processed.
