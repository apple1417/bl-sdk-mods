# bl-sdk-mods
To use these mods:
1. Install the Borderlands [PythonSDK](https://github.com/bl-sdk/PythonSDK)
2. Open the SDK Mods folder - launch the game, go into the new `Mods` menu, make sure you've got the `General` mod selected, and then press `O`
3. Download one of the mod zip files and open it
4. Copy the folder from inside the zip into the SDK Mods folder you just opened

If a folder doesn't have a zip file, or is not listed below, then the mod inside is likely incomplete. If you know what you're doing you can attempt to install it manually, but it may well have issues.

## Mods

### Always Offline
Forces the game to never download SHiFT hotfixes, meaning you can always safely use offline text mods.

### Apple's Borderlands Cheats
Adds keybinds performing various cheaty things. Currently contains:
- Infinite Ammo
- God Mode
- One Shot Mode
- Instant Cooldowns
- Passive Mode
- Free Shops
- Ghost Mode
- A 'Kill All' Button
- A 'Level Up' Button
- A 'Add OP Level' Button
- A 'Suicide' Button
- Teleport Between Fast Travels
- Teleport Between Level Transitions
- A 'Reset Shops' Button

Compatible with both BL2 and TPS.

### Enemy Level Randomizer
As the name might suggest, randomizes enemy levels. Probably a bad idea.

Note that this has a few options to let you customize the randomization. You can for example just turn randomization off and only add a pre-defined offset onto enemies' levels.

Compatible with both BL2 and TPS

### Hide Undiscovered Missions
A super simple mod that hides undiscovered missions in your mission log.

Compatible with both BL2 and TPS

### Item Level Uncapper
This mod is useless by itself, it should be used alongside the hexedit to increase the player level cap.    
Fixes the level cap of most items so that they continue spawning past level 100.    
Note that items past level 127 will overflow upon save-quit, and that Gibbed's Save Editor won't let you create items past 127, so past that point you'll have to pick up everything you use within the same session.    
Also note that there may still be various other issues with an increased level cap, this only fixes that most items stopped spawning.

Compatible with both BL2 and TPS.

### No Ads
Prevents ads from showing.
Includes both the obnoxious BL3 ads as well as the small MoTD DLC ads.

Compatible with both BL2 and TPS.

### Onezerker
Ever felt gunzerking with two different guns was too complicated? No? Well too bad. Makes you gunzerk with two copies of the same gun instead of two different ones.    
Thanks to FromDarkHell for finding the object which lets you gunzerk with only one equipped gun.

Only compatible with BL2 (obviously).

### Python Part Notifier
Shows the parts making up all of your items and weapons on their cards. Yes this even includes Grenades, COMs, and Relics/Oz Kits. Has full mod support, so if a mod adds extra parts to a weapon or changes a part's mesh it will properly update. Unique part support is limited, they may just have the same name as the base part with the same mesh.

What exactly is shown on the card is very customizable through the options menu. Don't care about a part slot? You can turn it off. Running out of space with all the parts you want to show? You can remove the original description. Or playing Randomizer and want to know what weapons each part comes from? Why not use detailed part names. All these options save between sessions, so you only have to set them up once.

Note that there are thousands of parts, so it's not impossible that the mod gets something wrong, don't be afraid to double check. If you do find an issue please report it alongside a gibbed code for the item.

Compatible with both BL2 and TPS.

### Rounds Per Minute
Makes item cards display rounds per minute rather than per second.

Compatible with both BL2 and TPS.

### Scaling Adjuster
A simple tool that adds an option to change the game's base scaling value. Your settings are saved between sessions    
Note that you may have to save quit for values to update.

Compatible with both BL2 and TPS.

### Side Mission Randomizer
Ever felt it was too easy to unlock all your favourite side missions? This mod randomizes their progression order. Turns the lovely (mostly) linear progression graph into a spaghetti nightmare.

This mod will create other mods in the sdk mod menu for each seed you generate, only one of which can be active at a time. If you want to share a seed with friends, select the main mod, open the settings file, and copy paste it over into their settings file.

If you want to spoil yourself you can also generate a dump of the exact mission progression.

Compatible with both BL2 and TPS.

### True Damage Logger
Prints the actual amount of damage you deal to console, bypassing visual damage cap.

Has a configurable minimum damage before logging, in case you don't want to spam your console.

Compatible with both BL2 and TPS.

## Libraries
These aren't mods by themselves, but other mods might make use of them.

### AsyncUtil
Adds a few simple functions to let you easily run callbacks in the future without hanging the game.

Compatible with both BL2 and TPS.

### Options Wrapper
As the name might suggest, a small wrapper for the default SDK options classes.

Adds proper inheritence between options - all options inherit from `Base`, boolean inherits from `Spinner`.
Gives each class an `IsHidden` attribute, so you don't need to create an instance of a completely new class to hide an option.

Replaces the default SDK options classes (hence the name being prefixed with `AAA_`, so it loads first).
It *should* be fully compatible with all existing calls, and have the exact same feature set (plus more).
If you really need one of the original classes however, they're stored under `OptionsWrapper.SDKOptions`.

Compatible with both BL2 and TPS.

### User Feedback
Adds several functions/classes to let you show various types of feedback to and get input from your users.

Currently includes:
1. Small messages on the left of the HUD, like those used for respawn cost messages.
2. Training dialog boxes in the middle of the screen, like those used for most training messages or the special edition item message.
3. Options boxes where the user can select from multiple different options, like those used to select playthrough or to confirm quitting.
4. A custom training box that takes text input.

Compatible with both BL2 and TPS.
