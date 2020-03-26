import unrealsdk
import importlib
import inspect
import os
import sys
from abc import ABC, abstractmethod
from typing import Any, Callable, ClassVar, cast, Dict, List

from Mods import AAA_OptionsWrapper as OptionsWrapper
from Mods import AsyncUtil
from Mods.UserFeedback import ShowHUDMessage

JSON = Dict[str, Any]


class BaseCrowdControlEffect(ABC):
    """
    Base class to be inherited from by all Crowd Control effects.

    Attributes:
        Name: The name of the effect. This must be unique.
        Description:
            The description of the effect. Displays as a the caption of an `OptionsBox`. Defaults to
            an empty string.
        HasConfigMenu:
            True if there should be a configure option when editing this effect. Defaults to False.
        Options:
            A list of `OptionsWrapper` options used to configure this effect, which will be shown in
            the plugins menu while this effect is enabled. Defaults to an empty list.
    """
    Name: ClassVar[str]
    Description: ClassVar[str] = ""
    HasConfigMenu: ClassVar[bool] = False
    Options: List[OptionsWrapper.Base]

    def __init__(self) -> None:
        """
        Creates the effect - make sure to call this method if you overwrite it. Does not take args.
        """
        self.Options = []

    @abstractmethod
    def OnRedeem(self, msg: JSON) -> None:
        """
        Callback function that must be overwritten. Called whenever someone redeems the reward
        associated with this effect.

        Args:
            msg:
                The decoded JSON channel points event message. See the following link for reference:
                https://dev.twitch.tv/docs/pubsub#receiving-messages
        """
        raise NotImplementedError

    def ShowConfiguration(self) -> None:
        """
        Callback function that must be overwritten if `HasConfigMenu` is True. Called whenever a
        user wants to configure this effect - should show it's own set of `UserFeedback` menus.
        """
        raise NotImplementedError

    def FinishConfiguration(self) -> None:
        """
        Function overwritten during mod configuration, used to return back to the original configure
        screen.
        """
        raise NotImplementedError

    def ShowRedemption(self, msg: JSON) -> None:
        """
        Small helper function that displays a UserFeedback HUDMessage with info about who redeemed
        this effect.

        Args:
            msg: The decoded JSON channel points event message.
        """
        def Internal() -> None:
            user = "Unknown user"
            try:
                user = msg["data"]["redemption"]["user"]["login"]
            except KeyError:
                pass
            ShowHUDMessage(
                "Crowd Control",
                f"{user} redeemed '{self.Name}'"
            )
        # There's a small delay after closing menus before we can properly show a message
        AsyncUtil.RunIn(0.1, Internal)


class QueuedCrowdControlEffect(BaseCrowdControlEffect):
    """
    Base class for Crowd Control Effects that should have queued activations. Only activates when
    the player is in game, but optionally allows this condition to be overwritten.

    Attributes:
        Interval: Default interval between activations, in seconds. Defaults to 15.
    """
    Interval: ClassVar[int] = 15

    _IntervalOption: OptionsWrapper.Slider
    _Queue: List[JSON]

    def __init__(self) -> None:
        """
        Creates the effect - make sure to call this method if you overwrite it. Does not take args.
        """
        super().__init__()

        self._IntervalOption = OptionsWrapper.Slider(
            Caption=f"{self.Name} Interval",
            Description=(
                "The minimum interval between activations, in seconds."
                " If the reward is redeemed twice within the interval, it will only activate a"
                " second time once it expires."
            ),
            StartingValue=self.Interval,
            MinValue=0,
            MaxValue=600,
            Increment=1
        )
        self.Options.append(self._IntervalOption)

        self._Queue = []

    @abstractmethod
    def OnRun(self, msg: JSON) -> None:
        """
        Callback function that must be overwritten. Called whenever one of the queued messages
        should be activated.

        Args:
            msg:
                The decoded JSON channel points event message. See the following link for reference:
                https://dev.twitch.tv/docs/pubsub#receiving-messages
        """
        raise NotImplementedError

    def OnRedeem(self, msg: JSON) -> None:
        """
        Callback function called whenever someone redeems the reward associated with this effect.
        This implementation adds messages to the queue - if you need to overwrite it make sure to
        call this function from your's.
        """
        def _RunFront() -> None:
            self.OnRun(self._Queue[0])
            AsyncUtil.RunIn(self._IntervalOption.CurrentValue, _Loop)

        def _Loop() -> None:
            self._Queue.pop(0)
            if len(self._Queue) > 0:
                AsyncUtil.RunWhen(self.Condition, _RunFront)

        self._Queue.append(msg)
        if len(self._Queue) == 1:
            AsyncUtil.RunWhen(self.Condition, _RunFront)

    def Condition(self) -> bool:
        """
        Specifies a condition for when this event is allowed to activate. By default this is only
        when the player is in game.

        Returns:
            bool: True if the effect may activate, False otherwise.
        """
        return IsInGame()


class DurationCrowdControlEffect(QueuedCrowdControlEffect):
    """
    Base class for Crowd Control Effects that have a duration, with callbacks on start/end.

    By making the Interval shorter than the Duration, additonal redeptions will restart the duration
    timer on these kinds of effects.

    Attributes:
        Duration: Default time the effect should be active for, in seconds. Defaults to 15.
    """
    Duration: ClassVar[int] = 15

    _DurationOption: OptionsWrapper.Slider

    def __init__(self) -> None:
        super().__init__()

        self._DurationOption = OptionsWrapper.Slider(
            Caption=f"{self.Name} Duration",
            Description=(
                "The duration of the effect."
                " If the duration is longer than the interval, addtional redemptions will restart "
                " the duration timer."
            ),
            StartingValue=self.Duration,
            MinValue=0,
            MaxValue=600,
            Increment=1
        )
        self.Options.append(self._DurationOption)

    def OnRun(self, msg: JSON) -> None:
        """
        Callback function for whenever a queued messages should be activated. This implementation
        makes sure the effect properly runs for the specified duration, so if you need to overwrite
        it make sure to call this function from your's.

        If the effect is already running then this function will restart the timer.
        """
        AsyncUtil.CancelFutureCallbacks(f"CC-{self.Name}-Stop")
        self.OnStart(msg)
        AsyncUtil.RunIn(self._DurationOption.CurrentValue, self.OnEnd, f"CC-{self.Name}-Stop")

    def OnStart(self, msg: JSON) -> None:
        """ Callback function that must be overwritten. Run when the effect starts. """
        raise NotImplementedError

    def OnEnd(self) -> None:
        """ Callback function that must be overwritten. Run when the effect ends. """
        raise NotImplementedError


def IsInGame() -> bool:
    """ Returns True if the player is in game, without being in any menus. """
    return not unrealsdk.GetEngine().GamePlayers[0].Actor.GFxUIManager.IsBlockingMoviePlaying()


def IsBL2() -> bool:
    """ Returns True if the game is currently BL2, False if it is TPS. """
    return cast(bool, unrealsdk.GetEngine().GetEngineVersion() == 8639)


""" Lists of callbacks for when the mod is enabled/disabled. """
ON_ENABLE: List[Callable[[], None]] = []
ON_DISABLE: List[Callable[[], None]] = []

""" A list with one instance of each defined effect. """
ALL_EFFECTS: List[BaseCrowdControlEffect] = []

_dir = os.path.dirname(__file__)
for file in os.listdir(_dir):
    if not os.path.isfile(os.path.join(_dir, file)):
        continue
    if file == "__init__.py":
        continue
    name, suffix = os.path.splitext(file)
    if suffix != ".py":
        continue

    effect = importlib.import_module(f".{name}", "Mods.CrowdControl.Effects")
    if f"Mods.CrowdControl.Effects.{name}" in sys.modules:
        importlib.reload(effect)
    for name, cls in inspect.getmembers(effect, inspect.isclass):
        # Filter out classes imported from other modules
        if inspect.getmodule(cls) != effect:
            continue
        # I can't use `issubclass()` because these are loaded from different files
        for c in inspect.getmro(cls)[1:]:
            if c.__name__ == BaseCrowdControlEffect.__name__:
                ALL_EFFECTS.append(cls())
                break
ALL_EFFECTS.sort(key=lambda e: e.Name)
