# Sanity Saver
Disables sanity check, and also saves items which don't serialize, which would have parts deleted
even with it off.

## Save Editing
This mod only saves parts which the game does not save itself. This means you can keep using any
regular save editor, for most cases. If you want to edit one of these parts which the game doesn't
save, and which get replaced by this, it gets a little more complex.

[See this video.](https://youtu.be/2p635l5C_KU)

### Opening Saves
All custom saves will be stored in the `Saves` folder within the mod's folder. The files here will
use the same numbers as in your normal saves folder, though the bank and stash are stored in
seperate files. To save on disk space, all files are compressed using gzip by default. You will
either need disable this in the mod options menu, or download something which can
compress/decompress them (e.g. [7zip](https://www.7-zip.org/)).

### Editing Items
Once you have your save file open, you should just be able to `Ctrl+F` the name of the item you want
to edit. A short description of every item you have is always stored, even if the mod doesn't
replace any of the parts on it. This description isn't modified after first being created, so you 
can edit it to be more clear if you want.

To change what parts the mod replaces you simply need to add new entries to the JSON object for your
item. The key should be the full name of the part slot, and the value should be the full path to the
part (or a number for the level).

The part slot names are:

Items                          | Weapons
-------------------------------|---------------------------
`ItemDefinition`               | `WeaponTypeDefinition`
`BalanceDefinition`            | `BalanceDefinition`
`ManufacturerDefinition`       | `ManufacturerDefinition`
`ManufacturerGradeIndex`       | `ManufacturerGradeIndex`
`AlphaItemPartDefinition`      | `BodyPartDefinition`
`BetaItemPartDefinition`       | `GripPartDefinition`
`GammaItemPartDefinition`      | `BarrelPartDefinition`
`DeltaItemPartDefinition`      | `SightPartDefinition`
`EpsilonItemPartDefinition`    | `StockPartDefinition`
`ZetaItemPartDefinition`       | `ElementalPartDefinition`
`EtaItemPartDefinition`        | `Accessory1PartDefinition`
`ThetaItemPartDefinition`      | `Accessory2PartDefinition`
`MaterialItemPartDefinition`   | `MaterialPartDefinition`
`PrefixItemNamePartDefinition` | `PrefixPartDefinition`
`TitleItemNamePartDefinition`  | `TitlePartDefinition`
`GameStage`                    | `GameStage`

### Adding New Items
To add a new item, you should first import it via a normal save editor and load into the game. Then
you can follow the instructions above to edit any extra parts you need to. The mod doesn't care what
the base item is, so if you want to replace every single slot you can just give it any random weapon
or item. You cannot however turn an item into a weapon, or vice versa.

### Why do some items have so many more slots listed than others?
Because the game's only tried to save them once.

The first time the mod comes across an item, it stores every single part slot. When the game loads
the item again, it then checks which parts saved properly. The mod doesn't need to deal with any
parts that the game saved properly, so it removes them from the list (making the save smaller).

You can still edit these large blocks just like the others, the parts the game saved won't match the
edits you make so the mod will note down that it needs to replace them. If you're still concerned,
or if you just want a cleaner item list, you can always quickly load back into the game or re-open
the bank/stash to update them.

## Changelog

### Sanity Saver v2.0
Changed the save file format a bit. Saves should automatically be migrated where possible.    
Made unserializable dropped items and items equipped by NPCs save over level transitions.    
Added option to reroll vendors on level transitions, to avoid unserialzable items breaking.    

### Sanity Saver v1.1
Fixed that the grinder and the SHiFT mailbox in tps would incorrectly be forced empty.    
Fixed that items with name parts that didn't have a name defined could cause custom saving to fail
entirely.

### Sanity Saver v1.0
Inital Release.
