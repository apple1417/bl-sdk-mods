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

Most structs just use their struct name directly. There are a few cases where this conflicts, when
this happens the name is prefixed with the outer object name(s) and underscore seperators - e.g.
`WillowGame.Behavior_AISetFlight:EFlightMode` and `WillowGame.WillowNavigationHandle:EFlightMode`
are accessible through `Behavior_AISetFlight_EFlightMode` and `WillowNavigationHandle_EFlightMode`
respectively.

If need be, you can access the unreal `Enum` object through the `._unreal` attribute.


# Changelog
## Enums v1.1
- Fixed that if two enums shared a name, only the last would be exposed - they now have a more
  verbose name, adding their outer object name if needed.
- Added the `._unreal` field to all enums.

## Enums v1.0
- Inital Release.
