import unrealsdk
import traceback
from datetime import datetime, timedelta
from typing import Any, Callable, ClassVar, Dict, List

from .SortedDict import SortedDict

VersionMajor: int = 1
VersionMinor: int = 1

Callback = Callable[[], Any]
Condition = Callable[[], bool]


_Callbacks: SortedDict[datetime, List[Callback]] = SortedDict({datetime.min: []})
_CallbackMap: Dict[str, List[Callback]] = {}


def _OnTick(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
    now = datetime.now()
    for time, callbk_list in _Callbacks.items():
        if time < now:
            for callbk in callbk_list:
                try:
                    callbk()
                except Exception:
                    unrealsdk.Log("[AsyncUtil] Exception thrown:")
                    for line in traceback.format_exc().split("\n"):
                        unrealsdk.Log(line)
            if time != datetime.min:
                del _Callbacks[time]
        else:
            break
    return True


unrealsdk.RunHook("WillowGame.WillowGameViewportClient.Tick", "AsyncUtil", _OnTick)


def RunIn(time: float, callbk: Callback, key: str = "") -> None:
    """
    Runs a callback in the provided amount of seconds.

    Args:
        time: The amount of time (in seconds) to wait before running the callback.
        callbk: The callback.
        key: An optional key to help identify the callback if you want to cancel it later.
    """
    if time <= 0:
        raise ValueError("RunIn() requires a non-zero, positive, time!")

    if len(key) == 0:
        key = str(callbk)
    if key in _CallbackMap:
        _CallbackMap[key].append(callbk)
    else:
        _CallbackMap[key] = [callbk]

    runAt = datetime.now() + timedelta(seconds=time)
    if runAt in _Callbacks:
        _Callbacks[runAt].append(callbk)
    else:
        _Callbacks[runAt] = [callbk]


def RunEvery(time: float, callbk: Callback, key: str) -> None:
    """
    Repeatedly runs a callback at the provided interval.

    Waits before running the callback the first time.

    Args:
        time: The amount of time (in seconds) to wait between running the callback.
        callbk: The callback.
        key: A key to help identify the callback to cancel it later.
    """
    if time <= 0:
        raise ValueError("RunEvery() requires a non-zero, positive, time!")

    def InnerCallback() -> None:
        callbk()
        RunIn(time, InnerCallback, key)
    RunIn(time, InnerCallback, key)


def RunEveryTick(callbk: Callback, key: str) -> None:
    """
    Repeatedly runs a callback every game tick.

    Args:
        callbk: The callback.
        key: A key to help identify the callback to cancel it later.
    """
    if key in _CallbackMap:
        _CallbackMap[key].append(callbk)
    else:
        _CallbackMap[key] = [callbk]
    _Callbacks[datetime.min].append(callbk)


def RunEveryWhile(time: float, cond: Condition, callbk: Callback, key: str) -> None:
    """
    Repeatedly runs a callback at the provided interval, as long as the provided condition holds.

    Waits before running the callback the first time.

    Args:
        time: The amount of time (in seconds) to wait between running the callback.
        cond: The conditon. Execution continues as long as this returns a truthy value.
        callbk: The callback.
        key: A key to help identify the callback to cancel it later.
    """
    if time <= 0:
        raise ValueError("RunEveryWhile() requires a non-zero, positive, time!")

    def InnerCallback() -> None:
        if cond():
            callbk()
            RunIn(time, InnerCallback, key)
    RunIn(time, InnerCallback, key)


def RunWhen(cond: Condition, callbk: Callback, key: str = "") -> None:
    """
    Runs a callback once the provided condition becomes true.

    Args:
        cond: The conditon. The callback is executed once this returns a truthy value.
        callbk: The callback.
        key: An optional key to help identify the callback if you want to cancel it later.
    """
    if len(key) == 0:
        key = str(callbk)

    def InnerCallback() -> None:
        if cond():
            callbk()
            CancelFutureCallbacks(key)
    RunEveryTick(InnerCallback, key)


def CancelFutureCallbacks(key: str) -> bool:
    """
    Cancels all future callbacks using the specified key.

    Args:
        key: The key of the callbacks to remove.
    """
    if key not in _CallbackMap:
        return False
    callbks = _CallbackMap[key]
    for time, val in _Callbacks.items():
        for callbk in val:
            if callbk in callbks:
                _Callbacks[time].remove(callbk)
    del _CallbackMap[key]
    return True


# Provide an entry in the mods list just so users can see that this is loaded
class _AsyncUtil(unrealsdk.BL2MOD):
    Name: ClassVar[str] = "AsyncUtil"
    Author: ClassVar[str] = "apple1417"
    Description: ClassVar[str] = (
        "Provides functionality for other mods, but does not do anything by itself."
    )
    Types: ClassVar[List[unrealsdk.ModTypes]] = [unrealsdk.ModTypes.Utility]
    Version: ClassVar[str] = f"{VersionMajor}.{VersionMinor}"

    Status: str
    SettingsInputs: Dict[str, str]

    def __init__(self) -> None:
        self.Author += "\nVersion: " + str(self.Version)  # type: ignore

        self.Status = "Enabled"
        self.SettingsInputs = {}


# Only register the mod on main menu, just to try keep it at the end of the list
def _OnMainMenu(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
    instance = _AsyncUtil()
    unrealsdk.RegisterMod(instance)
    if __name__ == "__main__":
        for i in range(len(unrealsdk.Mods)):
            if unrealsdk.Mods[i].Name == instance.Name:
                unrealsdk.Mods.remove(instance)
                unrealsdk.Mods[i] = instance
                break
    unrealsdk.RemoveHook("WillowGame.FrontendGFxMovie.Start", "AsyncUtil")
    return True


unrealsdk.RegisterHook("WillowGame.FrontendGFxMovie.Start", "AsyncUtil", _OnMainMenu)
