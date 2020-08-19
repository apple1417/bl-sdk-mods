import unrealsdk
from typing import ClassVar, Tuple, Optional
from .GFxMovie import GFxMovie


class TrainingBox(GFxMovie):
    """
    Class representing a training dialog box, like those used for the special edition items message
     (or most training messages but who looks at those).

    Attributes:
        Title: The title text to display at the top of the training box.
        Message: The message to display in the main caption of the training box.
        MinDuration:
            The amount of time the training box should display for before the user may close it.
        PausesGame: If the training box should pause the game while it is displayed.
        MenuHint:
            If to display a hint to open your menu, and what menu should be opened when you do.
             Defaults to 0, no hint. 1-5 represent the different the different menu tabs, in the
             same order as the game: Missions; Map; Inventory; Skills; BAR.
        Priority:
            A byte representing the priority of the training box in reference to the game's other
             `GfxMovie`s. Higher values display above lower ones.
    """

    Title: str
    Message: str
    MinDuration: float
    PausesGame: bool
    MenuHint: int
    Priority: int

    _TrainingBox: Optional[unrealsdk.UObject]
    _ExitKeys: ClassVar[Tuple[str, ...]] = (
        "Enter",
        "Escape",
        "LeftMouseButton",
        "XboxTypeS_A",
        "XboxTypeS_B",
        "XboxTypeS_Start",
    )

    def __init__(
        self,
        Title: str,
        Message: str = "",
        MinDuration: float = 0,
        PausesGame: bool = False,
        MenuHint: int = 0,
        Priority: int = 254,
    ) -> None:
        """
        Creates a training box.

        Args:
            Title: The title text to display at the top of the training box.
            Message:
                The message to display in the main caption of the training box. Defaults to the
                 empty string.
            MinDuration:
                The amount of time the training box should display for before the user may close it.
                 Defaults to 0.
            PausesGame:
                If the training box should pause the game while it is displayed. Defaults to False.
            MenuHint:
                If to display a hint to open your menu, and what menu should be opened when you do.
                 Defaults to 0, no hint. 1-5 represent the different the different menu tabs, in the
                 same order as the game: Missions; Map; Inventory; Skills; BAR. Defaults to 0.
            Priority:
                A byte representing the priority of the training box in reference to the game's
                 other `GfxMovie`s. Higher values display above lower ones. Defaults to 254, the
                  same as the game's default.
        """
        self.Title = Title
        self.Message = Message
        self.MinDuration = MinDuration
        self.PausesGame = PausesGame
        self.MenuHint = MenuHint
        self.Priority = Priority

        self._TrainingBox = None

    def Show(self) -> None:
        """ Displays the training box. """
        self._TrainingBox = unrealsdk.GetEngine().GamePlayers[0].Actor.GFxUIManager.ShowTrainingDialog(
            self.Message,
            self.Title,
            self.MinDuration,
            self.MenuHint,
            not self.PausesGame
        )
        self._TrainingBox.SetPriority(self.Priority)
        self._TrainingBox.ApplyLayout()

        def HandleInputKey(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if caller == self._TrainingBox:
                self.OnInput(params.ukey, params.uevent)

                # We don't have a good function to hook for when this exits so we have to decode it
                #  from the key presses
                if self._TrainingBox is not None and self._TrainingBox.DelayUntilShowOk < 0 and params.uevent == 1:
                    use_key = "FAKE"
                    if caller.GetPC().PlayerInput is not None:
                        use_key = caller.GetPC().PlayerInput.GetKeyForAction("Use", True)
                    if params.ukey in self._ExitKeys or params.ukey == use_key:
                        unrealsdk.RemoveHook("WillowGame.WillowGFxTrainingDialogBox.HandleInputKey", "CustomTrainingBox")
                        self._TrainingBox = None
                        self.OnExit()
            return True

        unrealsdk.RegisterHook("WillowGame.WillowGFxTrainingDialogBox.HandleInputKey", "CustomTrainingBox", HandleInputKey)

    def IsShowing(self) -> bool:
        """
        Gets if the training box is currently being displayed.

        Returns:
            True if the training box is currently being displayed, False otherwise.
        """
        return self._TrainingBox is not None

    def Hide(self) -> None:
        """
        Hides the training box, without running any callbacks.

        Displays a warning but does nothing if the training box is not currently being displayed.
        """
        if self._TrainingBox is None:
            unrealsdk.Log(
                "[UserFeedback] Warning: tried to hide a training box that was already closed"
            )
            return

        unrealsdk.RemoveHook("WillowGame.WillowGFxTrainingDialogBox.HandleInputKey", "CustomTrainingBox")

        # No nice GC trick this time, will get caught next cycle
        self._TrainingBox.Close()
        self._TrainingBox = None

    def OnExit(self) -> None:
        """ Callback function intended to be overwritten. Called when the training box closes. """
        pass
