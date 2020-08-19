## Exceptions
There are a few enemies which are not multiplied because doing so will cause softlocks.

- Thousand Cuts Brick - You can't hand in the note if there are extras.
- First Bunker autocannon - Extras will be invicible, but have to be killed to progress the quest.
- Claptrap worshippers - Extras will be friendly, but must be killed to progress the quest.
- Story kill Uranus - Extras don't spawn, but must be killed to open the doorway back.

## Changelog

### Spawn Multiplier v1.5
Updated to use some of the new features from SDK version 0.7.8.    
Most notably, the enabled state is now saved over game launches.

### Spawn Multiplier v1.4
Fixed a few places where enemy spawns had an additional cap, which will now be increased along with the others.    
Blacklisted a few enemies that would cause softlocks if multiplied.    
Fixed potential compatability issue with an upcoming version of the sdk.

### Spawn Multiplier v1.3
Prevented multiplying spawn counts for some non-enemy actors, which could cause softlocks in some cases (e.g. Burrows' generators).

### Spawn Multiplier v1.2
Fixed that spawn limit changes would not be reapplied on map change, they'd always revert to standard.    
Fixed some more instances where spawn counts would round down to 0.

### Spawn Multiplier v1.1
Fixed that changing the multiplier could occasionally round spawn counts down to 0.    
Fixed that disabling the mod would not revert spawn counts.

### Spawn Multiplier v1.0
Inital Release
