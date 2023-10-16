import unrealsdk
from typing import ClassVar, Dict, List, Optional, Tuple

from .GFxMovie import GFxMovie

import os
import sys

_lib_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ctypes")
sys.path.append(_lib_path)
from .ctypes import windll, create_string_buffer, memmove  # noqa: E402
sys.path.remove(_lib_path)


def _get_clipboard() -> Optional[str]:
    contents: Optional[str] = None
    windll.user32.OpenClipboard(None)
    handle = windll.user32.GetClipboardData(13)
    pcontents = windll.kernel32.GlobalLock(handle)
    size = windll.kernel32.GlobalSize(handle)
    if pcontents and size:
        raw_data = create_string_buffer(size)
        memmove(raw_data, pcontents, size)
        contents = raw_data.raw.decode('utf-16le').rstrip(u'\0')
    windll.kernel32.GlobalUnlock(handle)
    windll.user32.CloseClipboard()
    return contents


def _set_clipboard(contents: str) -> None:
    data = contents.encode('utf-16le')
    windll.user32.OpenClipboard(None)
    windll.user32.EmptyClipboard()
    handle = windll.kernel32.GlobalAlloc(0x0042, len(data) + 2)
    pcontents = windll.kernel32.GlobalLock(handle)
    memmove(pcontents, data, len(data))
    windll.kernel32.GlobalUnlock(handle)
    windll.user32.SetClipboardData(13, handle)
    windll.user32.CloseClipboard()


class TextInputBox(GFxMovie):
    """
    Class representing a custom dialog box that can be used to get text input. Based on the same
     UI element as `TrainingBox`, with heavy modification.

    Made for a standard US/Qwerty layout - non-ascii characters may not be recognised, and layouts
     that rearrange the shift symbols may find incorrect values being written.

    Attributes:
        Title: The title text to display at the top of the text input box.
        DefaultMessage: The default message that should be displayed when the box is first shown.
        PausesGame: If the text input box should pause the game while it is displayed.
        Priority:
            A byte representing the priority of the text input box in reference to the game's other
             `GfxMovie`s. Higher values display above lower ones.
    """

    Title: str
    DefaultMessage: str
    PausesGame: bool
    Priority: int

    # Store the message as a list of strings so that some 'characters' can actually be more than a
    #  single one, for the html escapes, and because it makes replacing chars in the middle easier
    _Message: List[str]
    _CursorPos: int
    _IsShiftPressed: bool
    _TrainingBox: Optional[unrealsdk.UObject]

    _SubmitKeys: ClassVar[Tuple[str, ...]] = (
        "Enter",
        "LeftMouseButton",
        "XboxTypeS_A",
        "XboxTypeS_Start",
    )
    _ExitKeys: ClassVar[Tuple[str, ...]] = (
        "Escape",
        "XboxTypeS_B",
    )
    _KeyMap: ClassVar[Dict[str, Tuple[str, str]]] = {
        # UnrealKeycode: (ValueIfLower, ValueIfUpper)
        "Add": ("+", "+"),
        "Subtract": ("-", "-"),
        "Multiply": ("*", "*"),
        "Divide": ("/", "/"),
        "One": ("1", "!"),
        "Two": ("2", "@"),
        "Three": ("3", "#"),
        "Four": ("4", "$"),
        "Five": ("5", "%"),
        "Six": ("6", "^"),
        "Seven": ("7", "&amp;"),
        "Eight": ("8", "*"),
        "Nine": ("9", "("),
        "Zero": ("0", ")"),
        "NumPadOne": ("1", "1"),
        "NumPadTwo": ("2", "2"),
        "NumPadThree": ("3", "3"),
        "NumPadFour": ("4", "4"),
        "NumPadFive": ("5", "5"),
        "NumPadSix": ("6", "6"),
        "NumPadSeven": ("7", "7"),
        "NumPadEight": ("8", "8"),
        "NumPadNine": ("9", "9"),
        "NumPadZero": ("0", "0"),
        "Backslash": ("\\", "|"),
        "Comma": (",", "&lt;"),
        "Decimal": (".", "."),
        "Equals": ("=", "+"),
        "LeftBracket": ("[", "{"),
        "Period": (".", "&gt;"),
        "Quote": ("'", "\""),
        "RightBracket": ("]", "}"),
        "Semicolon": (";", ":"),
        "Slash": ("/", "?"),
        "SpaceBar": (" ", " "),
        "Tab": ("\t", "\t"),
        "Tilde": ("`", "~"),
        "Underscore": ("-", "_"),
    }

    def __init__(
        self,
        Title: str,
        DefaultMessage: str = "",
        PausesGame: bool = False,
        Priority: int = 254
    ) -> None:
        """
        Creates a text input box.

        Args:
            Title: The title text to display at the top of the text input box.
            DefaultMessage:
                The default message that should be displayed when the box is first shown. Defaults
                 to the empty string.
            PausesGame:
                If the text input box should pause the game while it is displayed. Defaults to False.
            Priority:
                A byte representing the priority of the text input box in reference to the game's
                 other `GfxMovie`s. Higher values display above lower ones. Defaults to 254, the
                 same as the game's default.
        """
        self.Title = Title
        self.DefaultMessage = DefaultMessage
        self.PausesGame = PausesGame
        self.Priority = Priority

        self._Message = list(DefaultMessage)
        self._CursorPos = 0
        self._IsShiftPressed = False
        self._IsControlPressed = False
        self._TrainingBox = None

    def Show(self) -> None:
        """ Displays the text input box. """
        self._Message = list(self.DefaultMessage)
        self._CursorPos = len(self._Message)
        self._IsShiftPressed = False
        self._IsControlPressed = False

        self._TrainingBox = unrealsdk.GetEngine().GamePlayers[0].Actor.GFxUIManager.ShowTrainingDialog(
            self.DefaultMessage + "<u>  </u>",
            self.Title,
            0,
            0,
            not self.PausesGame
        )
        self._TrainingBox.SetPriority(self.Priority)
        self._TrainingBox.ApplyLayout()

        def HandleInputKey(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if caller != self._TrainingBox:
                return True
            self._HandleInput(params.ukey, params.uevent)
            self.OnInput(params.ukey, params.uevent)

            # Decode when we exit from keypresses
            if params.uevent == 1:
                if params.ukey in self._SubmitKeys:
                    unrealsdk.RemoveHook("WillowGame.WillowGFxTrainingDialogBox.HandleInputKey", "CustomTextInputBox")
                    self._TrainingBox = None
                    self.OnSubmit("".join(self._Message))
                elif params.ukey in self._ExitKeys:
                    unrealsdk.RemoveHook("WillowGame.WillowGFxTrainingDialogBox.HandleInputKey", "CustomTextInputBox")
                    self._TrainingBox = None
                    self.OnSubmit("")

            # Normally the use key causes exits too, block it
            use_key = "FAKE"
            if caller.GetPC().PlayerInput is not None:
                use_key = caller.GetPC().PlayerInput.GetKeyForAction("Use", True)
            return str(params.ukey) != use_key

        unrealsdk.RegisterHook("WillowGame.WillowGFxTrainingDialogBox.HandleInputKey", "CustomTextInputBox", HandleInputKey)

    def IsShowing(self) -> bool:
        """
        Gets if the text input box is currently being displayed.

        Returns:
            True if the text input box is currently being displayed, False otherwise.
        """
        return self._TrainingBox is None

    def Hide(self) -> None:
        """
        Hides the text input box, without running any callbacks.

        Displays a warning but does nothing if the text input box is not currently being displayed.
        """
        if self._TrainingBox is None:
            unrealsdk.Log(
                "[UserFeedback] Warning: tried to hide a text input box that was already closed"
            )
            return

        unrealsdk.RemoveHook("WillowGame.WillowGFxTrainingDialogBox.HandleInputKey", "CustomTextInputBox")

        self._TrainingBox.Close()
        self._TrainingBox = None

    def OnSubmit(self, Message: str) -> None:
        """
        Callback function intended to be overwritten. Called when the training box closes.

        Args:
            Message: The html-escaped message the user input. Note this may be the empty string.
        """
        pass

    def IsAllowedToWrite(self, Character: str, CurrentMessage: str, Position: int) -> bool:
        """
        Function called to determine if the character the user last input is may be added to the
         message, allowing for advanced input filtering.

        Args:
            Character: The html-escaped character the user just input.
            CurrentMessage: The current message, html-escaped, before adding the new character.
            Position: The position of the new character in the message.
        """
        return True

    def _HandleInput(self, key: str, event: int) -> None:
        """
        Function called any time the user inputs anything while the text input box is open.
        Responsible for converting keypresses into the typed message

        Args:
            key:
                The key that was pressed. See the following link for reference.
                https://api.unrealengine.com/udk/Three/KeyBinds.html#Mappable%20keys
            event:
                The input event type. See the following link for reference.
                https://docs.unrealengine.com/en-US/API/Runtime/Engine/Engine/EInputEvent/index.html
        """

        if key in ("LeftShift", "RightShift"):
            if event == 0:
                self._IsShiftPressed = True
            elif event == 1:
                self._IsShiftPressed = False
            return

        if key in ("LeftControl", "RightControl"):
            if event == 0:
                self._IsControlPressed = True
            elif event == 1:
                self._IsControlPressed = False
            return

        if event != 0 and event != 2:
            return

        if self._IsControlPressed:
            if key == "C":
                _set_clipboard("".join(self._Message))
                return
            elif key == "X":
                _set_clipboard("".join(self._Message))
                self._Message = []
                self._CursorPos = 0
            elif key == "V":
                clipboard = _get_clipboard().replace("\r\n", "\n")
                if clipboard is None or clipboard == "":
                    return
                for character in clipboard:
                    if not self.IsAllowedToWrite(character, "".join(self._Message), self._CursorPos):
                        break
                    self._Message.insert(self._CursorPos, character)
                    self._CursorPos += 1
            else:
                return
        elif key == "Left":
            self._CursorPos = max(self._CursorPos - 1, 0)
        elif key == "Right":
            self._CursorPos = min(self._CursorPos + 1, len(self._Message))
        elif key == "Home":
            self._CursorPos = 0
        elif key == "End":
            self._CursorPos = len(self._Message)
        elif key == "BackSpace":
            if self._CursorPos != 0:
                del self._Message[self._CursorPos - 1]
                self._CursorPos -= 1
        elif key == "Delete":
            if self._CursorPos != len(self._Message):
                del self._Message[self._CursorPos]
        else:
            if key in self._KeyMap:
                key = self._KeyMap[key][self._IsShiftPressed]
            elif key in "QWERTYUIOPASDFGHJKLZXCVBNM":
                if not self._IsShiftPressed:
                    key = key.lower()
            else:
                return
            if not self.IsAllowedToWrite(key, "".join(self._Message), self._CursorPos):
                return
            self._Message.insert(self._CursorPos, key)
            self._CursorPos += 1

        # Draw the updated box
        if self._TrainingBox is None:
            return

        # For the sake of consistency with other movies in this library, we don't want to update the
        #  title if you changed the attribute, so read it from the training box instead
        title = self._TrainingBox.DlgCaptionMarkup

        # Add some spaces to render the cursor under if needed
        message = list(self._Message) + ["  "]
        message[self._CursorPos] = "<u>" + message[self._CursorPos] + "</u>"

        self._TrainingBox.SetText(title, "".join(message))
        self._TrainingBox.ApplyLayout()
