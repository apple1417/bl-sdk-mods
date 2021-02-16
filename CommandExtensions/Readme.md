# Command Extensions
Adds a few new console commands, and provides functionality for other mods to do the same. All these
commands are fully compatible with blcmm files, you can just put them in your mod and have users
merge it with other files and enable/disable various categories and it all just keeps working fine.

[See here for info on the builtin commands and how to write mods using them.](Writing-Mods.md)

### Multiplayer Compatability
Multiplayer compatability largely depends on the exact mod making use of this. Some commands are
simply incompatibly with multiplayer, anything relying on them too much will not work. Like always,
all players should make sure to be running the exact same set of mods, even more so than normally.

### Why does it take so much longer to `exec` my mods now?
This mod has to look through your mod file to handle the extra commands, which just takes some
extra, unavoidable, time. You can speed it up by making your mod file smaller - enable structural
edits then delete any categories you don't have enabled (and won't suddenly re-enable soon).

A more optimized file parser is being worked on, but it will never remove all the extra time.

## Changelog

### Command Extensions v1.1
Added the `CE_Debug`, `clone_bpd`, and `set_material` commands.    
Explicitly raise errors when a mod tries to register `set` or unregister `CE_EnableOn` - neither of
these worked properly in the first place.    
Switched the demo mod file to "online" mode.

### Command Extensions v1.0
Inital Release.
