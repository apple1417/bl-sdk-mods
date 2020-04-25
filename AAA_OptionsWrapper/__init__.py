import unrealsdk
from abc import ABC
from typing import Any, ClassVar, Dict, List, Sequence, Tuple

from Mods.SaveManager import storeModSettings  # type: ignore

VersionMajor: int = 1
VersionMinor: int = 1


class Base(ABC):
    """
    The abstract base class used for all options.

    Attributes:
        Caption: The name of the option.
        IsHidden:
            If the option should be hidden from the menu. If hidden it will still be saved to the
            settings file.
        CurrentValue: The current value of the option.

        EventID: Used for compatability with the existing options system, don't modify it
        OptionType: Used for compatability with the existing options system, don't modify it
    """
    Caption: str
    IsHidden: bool
    _CurrentValue: Any

    _EventID: int
    _OptionType: int

    @property
    def CurrentValue(self) -> Any:
        return self._CurrentValue

    @CurrentValue.setter
    def CurrentValue(self, val: Any) -> None:
        self._CurrentValue = val
        storeModSettings()

    @property
    def EventID(self) -> int:
        return -700000 if self.IsHidden else self._EventID

    @EventID.setter
    def EventID(self, val: int) -> None:
        self._EventID = val

    @property
    def OptionType(self) -> int:
        return -1 if self.IsHidden else self._OptionType

    @OptionType.setter
    def OptionType(self, val: int) -> None:
        self._OptionType = val


class Hidden(Base):
    """ An option that is always hidden. """
    def __init__(self, valueName: str, StartingValue: Any):
        """
        Creates the Hidden option.

        Args:
            valueName: The name of the option.
            StartingValue: The value the option should be initalized to.
        """
        self.Caption = valueName
        self.CurrentValue = StartingValue

    @property  # type: ignore
    def IsHidden(self) -> bool:  # type: ignore
        return True

    @IsHidden.setter
    def IsHidden(self, val: bool) -> None:
        pass


class Slider(Base):
    """
    An option which allows users to select a value along a slider.

    Note that unlike the SDK Option this replaces, all the values are typed as ints, not floats.
    This is because, while the slider accepts float inputs, it will only ever output ints. This is
     not an issue with the options implementation, the unrealscript outputs ints.
    You can pass in floats and it will continue working as before, but if you're using a type
     checker it will hopefully warn you, likely eventually leading you to this description.

    Attributes:
        Caption: The name of the option.
        IsHidden:
            If the option should be hidden from the menu. If hidden it will still be saved to the
            settings file.
        CurrentValue: The current value of the option.
        Description:
            The description to display at the bottom of the options menu when this option is
            selected.
        StartingValue: The inital value of the slider.
        MinValue: The minimum value that the slider can be set to.
        MaxValue: The maximum value that the slider can be set to.
        Increment: How far each tick on the slider changes the value.

        EventID: Used for compatability with the existing options system, don't modify it
        OptionType: Used for compatability with the existing options system, don't modify it
    """
    Description: str
    StartingValue: int
    MinValue: int
    MaxValue: int
    Increment: int

    def __init__(
        self,
        Caption: str,
        Description: str,
        StartingValue: int,
        MinValue: int,
        MaxValue: int,
        Increment: int,
        IsHidden: bool = False,
    ) -> None:
        """
        Creates the slider.

        Args:
            Caption: The name of the option.
            Description: The option's description.
            StartingValue: The inital value of the slider.
            MinValue: The minimum value that the slider can be set to.
            MaxValue: The maximum value that the slider can be set to.
            Increment: How far each tick on the slider changes the value.
            IsHidden: If the option should be hidden from the menu. Defaults to False.
        """
        self.Caption = Caption
        self.Description = Description
        self.StartingValue = StartingValue
        self.CurrentValue = StartingValue
        self.MinValue = MinValue
        self.MaxValue = MaxValue
        self.Increment = Increment
        self.IsHidden = IsHidden

        self._EventID = 0
        self._OptionType = 3

    @property
    def CurrentValue(self) -> Any:
        return self._CurrentValue

    @CurrentValue.setter
    def CurrentValue(self, val: Any) -> None:
        # The sdk options handler will convert an int to a float, so convert it abck
        self._CurrentValue = int(val)
        storeModSettings()


class Spinner(Base):
    """
    An option which allows users to select one value from a set of strings.

    Attributes:
        Caption: The name of the option.
        IsHidden:
            If the option should be hidden from the menu. If hidden it will still be saved to the
            settings file.
        CurrentValue: The current value of the option, as a string.
        Description:
            The description to display at the bottom of the options menu when this option is
            selected.
        StartingChoice: The initally selected choice.
        Choices: A sequence of strings to be used as the choices.

        EventID: Used for compatability with the existing options system, don't modify it
        OptionType: Used for compatability with the existing options system, don't modify it
    """

    Description: str
    StartingChoice: str
    Choices: Sequence[str]

    def __init__(
        self,
        Caption: str,
        Description: str,
        StartingChoice: str,
        Choices: Sequence[str],
        IsHidden: bool = False,
    ) -> None:
        """
        Creates the Spinner.

        Args:
            Caption: The name of the option.
            Description: The option's description.
            StartingChoice: The initally selected choice.
            Choices: A sequence of strings to be used as the choices.
            IsHidden: If the option should be hidden from the menu. Defaults to False.
        """
        self.Caption = Caption
        self.Description = Description
        self.StartingChoice = StartingChoice
        self.CurrentValue = StartingChoice
        self.Choices = Choices
        self.IsHidden = IsHidden

        self._EventID = 0
        self._OptionType = 0


# The existing version of this is by far the worst piece of code I've seen in the whole mod manager
# Why on earth wouldn't you natively subclass spinner
# Why on earth do you store indexes instead of values like the spinner - there's a conversion
#  sepecifically for this case why not just use the same code for both
# WHY ON EARTH DO YOU STORE A BOOL INTO CURRENTVALUE AFTER IT CHANGES WHEN IT'S AN INT AT FIRST
class Boolean(Spinner):
    """
    A special form of a spinner, with two options representing boolean values.

    Attributes:
        Caption: The name of the option.
        IsHidden:
            If the option should be hidden from the menu. If hidden it will still be saved to the
            settings file.
        CurrentValue: The current value of the option, as a boolean value.
        Description:
            The description to display at the bottom of the options menu when this option is
            selected.
        StartingChoice: The inital value of the option, as a boolean value.
        StartingChoiceIndex:
            The index of the inital value of the option - 0 for False, 1 for True. Used for
            compatability with the existing options system
        Choices: A tuple of two strings, index 0 being the False choice, index 1 being the True one.

        EventID: Used for compatability with the existing options system, don't modify it
        OptionType: Used for compatability with the existing options system, don't modify it
    """
    Choices: Tuple[str, str]

    StartingChoiceIndex: int

    def __init__(
        self,
        Caption: str,
        Description: str,
        StartingValue: bool,
        IsHidden: bool = False,
        Choices: Tuple[str, str] = ("Off", "On")
    ) -> None:
        """
        Creates the boolean spinner.

        Args:
            Caption: The name of the option.
            Description: The option's description.
            StartingValue: The initally value of the spinner.
            IsHidden: If the option should be hidden from the menu. Defaults to False.
            Choices: A tuple of two strings to be used to represent the value. Defaults to Off/On.
        """
        self.Caption = Caption
        self.StartingChoiceIndex = int(StartingValue)
        self.CurrentValue = StartingValue
        self.Description = Description
        self.IsHidden = IsHidden
        self.Choices = Choices

        self._EventID = 0
        self._OptionType = 0

    @property  # type: ignore
    def StartingChoice(self) -> bool:  # type: ignore
        return bool(self.StartingChoiceIndex)

    @StartingChoice.setter
    def StartingChoice(self, val: bool) -> None:
        self.StartingChoiceIndex = int(val)

    @property
    def CurrentValue(self) -> Any:
        return self._CurrentValue

    @CurrentValue.setter
    def CurrentValue(self, val: Any) -> None:
        self._CurrentValue = bool(val)
        storeModSettings()


class SDKOptions:
    Slider = unrealsdk.Options.Slider
    Spinner = unrealsdk.Options.Spinner
    Boolean = unrealsdk.Options.Boolean
    Hidden = unrealsdk.Options.Hidden


unrealsdk.Options.Slider = Slider
unrealsdk.Options.Spinner = Spinner
unrealsdk.Options.Boolean = Boolean
unrealsdk.Options.Hidden = Hidden


# Provide an entry in the mods list just so users can see that this is loaded
class _OptionsWrapper(unrealsdk.BL2MOD):
    Name: ClassVar[str] = "OptionsWrapper"
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
    instance = _OptionsWrapper()
    unrealsdk.RegisterMod(instance)
    if __name__ == "__main__":
        for i in range(len(unrealsdk.Mods)):
            if unrealsdk.Mods[i].Name == instance.Name:
                unrealsdk.Mods.remove(instance)
                unrealsdk.Mods[i] = instance
                break
    unrealsdk.RemoveHook("WillowGame.FrontendGFxMovie.Start", "OptionsWrapper")
    return True


unrealsdk.RegisterHook("WillowGame.FrontendGFxMovie.Start", "OptionsWrapper", _OnMainMenu)
