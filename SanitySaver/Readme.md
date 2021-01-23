# Sanity Saver
Disables sanity check, and also saves items which don't serialize, which would have parts deleted
even with it off.

## Save Editing
This mod only saves parts which the game does not save itself. This means you can keep using any
regular save editor in most cases. If you want to edit one of these parts which the game doesn't
save though, you'll have to delve into the custom save format.

### Opening Saves
All custom saves will be stored in the `Saves` folder within the mod's folder. The files here will
use the same numbers as in your normal saves folder, though the bank and stash are stored in
seperate files. To save on disk space, all files are compressed using gzip by default. You will
either need disable this, or download something which can compress/decompress them (e.g. 
[7zip](https://www.7-zip.org/)). To disable compression, find the `settings.json` in the main mod
folder, set `CompressSaves` to `true`, and re-launch the game.

### Editing Items
Once you have your save file open, you should just be able to `Ctrl+F` the name of the weapon you
want to edit. The level/name of every item you have is always stored, even if the mod doesn't
replace any of the parts on it. To change what parts the mod replaces you simply need to add new
keys to the JSON object for your item. They key should be the full name of the part slot, and the
value should be the full path to the part (or a number for the level).

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
Because you haven't loaded back into the game after a sq since obtaining them, or because you
haven't re-opened the bank/stash.

The first time the mod comes across an item, it stores every single part slot. When the game loads
the item again, it then checks which parts saved properly. The mod doesn't need to deal with any
parts that the game saved properly, so it removes them from the list (making the save smaller).

You can still edit these large blocks just like the others, the parts the game saved won't match the
edits you make so the mod will note down that it needs to replace them. If you're still concerned,
or if you just want a cleaner item list, you can always quickly load back into the game or re-open
the bank/stash to update them.

## Changelog

### Sanity Saver v1.0
Inital Release.
