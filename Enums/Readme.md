# Enums
Imports all Unrealscript enums into Python.

When you see the Unrealscript:
```cs
enum ENetMode {
    NM_Standalone,
    NM_DedicatedServer,
    NM_ListenServer,
    NM_Client,
    NM_MAX
};
```

You can use the Python:
```py
from Mods.Enums import ENetMode
...
if world_info.NetMode == ENetMode.NM_Client:
    pass
```

# Changelog
## Enums v1.0
Inital Release.
