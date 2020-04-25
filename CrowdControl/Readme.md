# Borderlands Crowd Control

## How it works
Borderlands Crowd Control contains a number of effects that you can choose to have activated when certain channel points rewards are redeemed. Each effect has a trigger phrase. While the mod is active, it will listen for any custom channel point reward redemptions, and it will check if that reward's title matches up with any of the trigger phrases. Any effects that it matches will be activated - though effects may chose to queue the activation for later. Multiple effects can share the same trigger phrase, though this may have unintended interactions.

There are some limitations with this approach:
- Rewards have to be setup manually.
- Rewards cannot be refunded.
- Rewards can only be processed in real time - if the mod is not running or your connections drops any redemptions will be ignored.
- If you quit the game while a reward is queued, it will be lost.

## Setup
Crowd Control has a lot more setup than other SDK mods. This section explains the full setup from a completely fresh install.

Firstly, install the SDK:

1. [Download the latest SDK release here](https://github.com/bl-sdk/PythonSDK/releases).
   Make sure that you download `PythonSDK.zip`, *not* either source code link.
   The correct file should only contain a few dlls, a zip file, and a "Mods" folder.
2. Open up the game's folder - in Steam right click the game, properties -> local
   files -> browse local files - and browse to `Binaries/Win32`.
   This should be the folder containing the game's exe.
3. Extract all the files from inside the zip you downloaded to this folder.

Crowd Control also requires Python to be installed locally, and to be added on your `PATH`. It requires at least Python 3.7, as well as `pip`.

1. [Download a compatible Python release from here](https://www.python.org/downloads/). Remember you need at leasy Python 3.7.
2. On the first screen of the installer, make sure to tick the box to add it to your `PATH`:
   ![Highlighted Checkbox](https://i.imgur.com/y4IC5Ee.png)
3. Work through the rest of the installer. If you customize the installation, make sure to install `pip`.

Next, actually install Crowd Control:

1. Download the latest releases of:    
   [Crowd Control](https://github.com/apple1417/bl-sdk-mods/raw/master/CrowdControl/CrowdControl.zip)    
   [AsyncUtil](https://github.com/apple1417/bl-sdk-mods/raw/master/AsyncUtil/AsyncUtil.zip)    
   [OptionsWrapper](https://github.com/apple1417/bl-sdk-mods/raw/master/AAA_OptionsWrapper/OptionsWrapper.zip)    
   [UserFeedback](https://github.com/apple1417/bl-sdk-mods/raw/master/UserFeedback/UserFeedback.zip)    
2. Back in the game folder, browse to `Binaries/Win32/Mods` - this should be one of the folders you extracted from the SDK.
3. Copy all folders out of the various zip files into this Mods folder.
4. Browse into `Binaries/Win32/Mods/CrowdControl`, which you just extracted.
5. Double click `install.py` to run it, then follow the instructions it gives you.

At this point the mod should be properly installed, but you will still have to configure your channel rewards. Start off by configuring the mod in game:

1. Launch the game and get to the main menu
2. Open up the new "Mods" menu.
3. Select `BLCC`, then press `C` to start configuring effects. You can use this menu to enable/disable effects, as well as change their trigger.    
   ![Configure Menu](https://i.imgur.com/rUP1cf9.png)
4. Next enable the mod, then head to the options menu, and into the new "Plugins" menu. Here you can perform some extra configuration.    
   ![Options Menu](https://i.imgur.com/SK95AMn.png)

Next, go to your Twitch settings and the custom rewards. [Visit the "Manage Rewards" page here](https://dashboard.twitch.tv/u/apple1417/community/channel-points/rewards), and add them. Generally you can completely customize all the options, but there are a few things to keep in mind:

- The title must match the trigger exactly (except for case). If it doesn't then the effect will never run.
- "Skip Reward Requests Queue" should probably be on - the mod can't mark rewards as complete, but it will properly process all of them.
- Some effects may have extra, specific requirements.

Finally, go back to the mod menu and press `Enter` to enable the mod. This will create a python console in the background, running the listener program. This program has to stay open for the mod to run, if you close it the mod will disable itself. It should close itself when you disable the mod or close the game, but in some cases it may keep running. Steam will see this window as being part of the game, and will consider you to be playing the game until you close it.

## Effect Packs
Effects are setup in such a way that other developers can easily create their own effects and effect packs to expand upon this mod. To install them:

1. Download the effect/effect pack from whatever source you found it. This should be a collection of one or more `.py` files.
2. Open up your game directory and navigate to `Binaries/Win32/Mods/CrowdControl/Effects`
3. Copy all the `.py` files into this folder.
4. Restart the game

### For Devs
All effects are loaded from this `Effects` folder. Any subclass of `BaseCrowdControlEffect` will be loaded. You can put multiple classes in a single file, or spread them all out, they'll be loaded all the same. In the `__init__.py` you can find docstrings explaining how exactly to use the class, as well as some helpful subclasses and methods.

This mod already requires `AsyncUtil`, `OptionsWrapper`, and `UserFeedback`, you can safely use any of them as part of your effect. If you require any other libraries make sure to explain how to install them in your own instructions.

## Changelog
### Borderlands Crowd Control v1.0
Inital Release
