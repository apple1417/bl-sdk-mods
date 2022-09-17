# Enums
Imports all Unrealscript structs into Python, as named tuples. Structs can be constructed using
their fields, or constructed directly from an Unrealscript struct.

```py
from Mods.Structs import Vector

pawn.Location = Vector(Y=1000)

loc = Vector(pawn.Location)
pawn.Location = loc._replace(Z=500)
```

All fields default to the relevant zero-value - including nested structs automatically defaulting to
the relevant nested named tuple.

Most structs just use their struct name directly. There are a few cases where this conflicts, when
this happens the name is prefixed with the outer object name(s) and underscore seperators - e.g.
`Engine.NavigationPoint:CheckpointRecord` and `Engine.PhysicsVolume:CheckpointRecord` are accessible
through `NavigationPoint_CheckpointRecord` and `PhysicsVolume_CheckpointRecord` respectively.

If need be, you can access the unreal `ScriptStruct` through the `._unreal` attribute.

# Changelog
## Structs v1.0
- Inital Release.
