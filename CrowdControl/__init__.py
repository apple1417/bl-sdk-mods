import unrealsdk
import json
import msvcrt
import subprocess
import sys
import webbrowser
from dataclasses import dataclass
from os import path
from typing import Any, ClassVar, Dict, IO, List, Optional

try:
    from Mods import AAA_OptionsWrapper as OptionsWrapper
    from Mods import AsyncUtil
    from Mods.UserFeedback import ShowHUDMessage, OptionBox, OptionBoxButton, TextInputBox, TrainingBox
except ImportError as ex:
    webbrowser.open("https://apple1417.github.io/bl2/didntread/?m=Borderlands%20Crowd%20Control&au&ow&uf")
    raise ex

from Mods.CrowdControl import Effects

if __name__ == "__main__":
    import importlib
    importlib.reload(sys.modules["Mods.CrowdControl.Effects"])
    importlib.reload(sys.modules["Mods.AsyncUtil"])
    importlib.reload(sys.modules["Mods.UserFeedback"])

    # See https://github.com/bl-sdk/PythonSDK/issues/68
    try:
        raise NotImplementedError
    except NotImplementedError:
        __file__ = sys.exc_info()[-1].tb_frame.f_code.co_filename  # type: ignore

_native_path = path.join(path.dirname(__file__), "Native")
if _native_path not in sys.path:
    sys.path.append(_native_path)

from ctypes import byref  # noqa

if sys.platform == "win32":
    from os import startfile
    from subprocess import STARTUPINFO

    from ctypes import GetLastError, windll, WinError
    from ctypes.wintypes import BYTE, DWORD
else:
    raise ImportError("This mod relies on several windows-specific functions, it simply won't work on other platforms.")

    # Mypy can't take a hint
    from ctypes import c_byte, c_ulong
    windll: Any  # This one's complicated
    BYTE = c_byte
    DWORD = c_ulong

    def GetLastError() -> int:
        return 0

    def WinError() -> WindowsError:
        return WindowsError()

    def startfile(path: str) -> None:
        pass

    class STARTUPINFO:
        dwFlags: int
        wShowWindow: int


def GetPipeAvailableLen(pipe: IO[Any]) -> int:
    handle = msvcrt.get_osfhandle(pipe.fileno())

    buf = (BYTE * 16)()
    read = DWORD(0)
    available = DWORD(0)
    left = DWORD(0)

    res = windll.kernel32.PeekNamedPipe(
        handle,
        byref(buf),
        1,
        byref(read),
        byref(available),
        byref(left)
    )

    if res == 0:
        if GetLastError() == 109:  # ERROR_BROKEN_PIPE
            return 0
        raise WinError()

    return available.value


class CrowdControl(unrealsdk.BL2MOD):
    Name: ClassVar[str] = "BLCC"
    Author: ClassVar[str] = "apple1417"
    Description: ClassVar[str] = (
        "<font size='24' color='#FFDEAD'>Borderlands Crowd Control</font>\n"
        "Lets viewers on Twitch spend channel points to affect your game."
    )
    Types: ClassVar[List[unrealsdk.ModTypes]] = [unrealsdk.ModTypes.Content, unrealsdk.ModTypes.Gameplay]
    Version: ClassVar[str] = "1.1"

    SettingsInputs: Dict[str, str]
    Options: List[OptionsWrapper.Base]

    TOKEN_URL: ClassVar[str] = "https://apple1417.github.io/bl2/crowdcontrol/"

    BASE_PATH: ClassVar[str] = path.dirname(path.realpath(__file__))
    TOKEN_FILE: ClassVar[str] = path.join(BASE_PATH, "token.txt")
    TRIGGER_FILE: ClassVar[str] = path.join(BASE_PATH, "config.json")

    Token: Optional[str]

    @dataclass
    class _Trigger():
        Effect: Effects.BaseCrowdControlEffect
        Trigger: str
        IsEnabled: bool

    Triggers: List[_Trigger]

    _listener: Optional[subprocess.Popen]  # type: ignore
    LatestFatalError: Optional[TrainingBox]

    def __init__(self) -> None:
        # Hopefully I can remove this in a future SDK update
        self.Author += "\nVersion: " + str(self.Version)  # type: ignore

        self.SettingsInputs = {
            "Enter": "Enable",
            "C": "Configure Effects",
            "G": "Generate Token"
        }

        try:
            self.Token = open(self.TOKEN_FILE).read().strip()
        except FileNotFoundError:
            self.Token = None

        self.LoadTriggers()
        self._listener = None
        self.LatestFatalError = None

    def LoadTriggers(self) -> None:
        self.Options = []
        self.Triggers = []
        trigger_dict = {}
        try:
            with open(self.TRIGGER_FILE) as file:
                trigger_dict = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        for effect in Effects.ALL_EFFECTS:
            trig = CrowdControl._Trigger(effect, effect.Name, True)
            if effect.Name in trigger_dict:
                trig.Trigger = trigger_dict[effect.Name]["Trigger"]
                trig.IsEnabled = trigger_dict[effect.Name]["IsEnabled"]
                for option in effect.Options:
                    option.IsHidden = not trig.IsEnabled
                    self.Options.append(option)
            self.Triggers.append(trig)
        self.Triggers.sort(key=lambda x: x.Effect.Name)
        self.SaveTriggers()

    def SaveTriggers(self) -> None:
        trigger_dict = {}
        for trig in self.Triggers:
            trigger_dict[trig.Effect.Name] = {
                "Trigger": trig.Trigger,
                "IsEnabled": trig.IsEnabled
            }
        with open(self.TRIGGER_FILE, "w") as file:
            json.dump(trigger_dict, file, indent=2)

    def SettingsInputPressed(self, name: str) -> None:
        if name == "Enable" and self.Token is not None:
            self.Status = "Enabled"
            self.SettingsInputs["Enter"] = "Disable"
            self.Enable()
        elif name == "Disable":
            self.Status = "Disabled"
            self.SettingsInputs["Enter"] = "Enable"
            self.Disable()
        elif name == "Configure Effects":
            self.Configure()
        elif name == "Generate Token":
            self.GenerateToken()

    def Enable(self) -> None:
        if self.Token is None:
            return

        startupinfo = STARTUPINFO()
        startupinfo.dwFlags |= 1  # STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 7  # SW_SHOWMINNOACTIVE

        self._listener = subprocess.Popen(
            ["python", "-m", "Listener", self.Token],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self.BASE_PATH,
            startupinfo=startupinfo
        )

        def OnTick() -> None:
            if self._listener is None:
                return
            if self._listener.poll() is not None:
                # Since the lister has quit we can safely call read without blocking
                # Only do this on stderr though cause that's where exceptions go
                line = self._listener.stderr.read()
                if len(line) > 0:
                    self.HandleStderr(line.decode("utf8").replace("\\n", "\n")[:-2])
                self.HandleChildQuit()
                return

            if GetPipeAvailableLen(self._listener.stdout) > 0:
                line = self._listener.stdout.readline()
                self.HandleStdout(line.decode("utf8").replace("\\n", "\n")[:-2])

            if GetPipeAvailableLen(self._listener.stderr) > 0:
                line = self._listener.stderr.readline()
                self.HandleStderr(line.decode("utf8").replace("\\n", "\n")[:-2])

        def OnQuit(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if self._listener is not None:
                self._listener.kill()

            return True

        AsyncUtil.RunEveryTick(OnTick, "CrowdControl")
        unrealsdk.RegisterHook("WillowGame.FrontendGFxMovie.ConfirmQuit_Clicked", "CrowdControl", OnQuit)

        for callback in Effects.ON_ENABLE:
            callback()

    def Disable(self) -> None:
        AsyncUtil.CancelFutureCallbacks("CrowdControl")
        unrealsdk.RemoveHook("WillowGame.FrontendGFxMovie.ConfirmQuit_Clicked", "CrowdControl")
        if self._listener is not None:
            self._listener.kill()
            self._listener = None

        for callback in Effects.ON_DISABLE:
            callback()

    def ShowMessage(self, msg: str) -> None:
        ShowHUDMessage(
            Title=self.Name,
            Message=msg
        )

    def ShowFatalError(self, msg: str) -> None:
        box = TrainingBox(
            Title=f"{self.Name}: Fatal Error",
            Message=f"{msg}\n\nMod will now disable.",
            PausesGame=True
        )

        def OnExit() -> None:
            self.LatestFatalError = None
        box.OnExit = OnExit  # type: ignore

        # If there are other errors showing then queue this one up, don't stack boxes
        if self.LatestFatalError is None:
            box.Show()
        else:
            def OnCurrentExit() -> None:
                box.Show()
            self.LatestFatalError.OnExit = OnCurrentExit  # type: ignore
        self.LatestFatalError = box

    # You know I probably should have split these menus into their own files this is a mess
    def Configure(self) -> None:
        toggleEnabledButton = OptionBoxButton("Toggle Enabled")
        editTriggerButton = OptionBoxButton(
            "Edit Trigger",
            "Edits what redemption title triggers this effect. Not case sensitive, but must match exactly otherwise."
        )
        extraConfigurationButton = OptionBoxButton(
            "Extra Options",
            "Adjust extra, effect specific options."
        )

        def GetCaptionStr(trig: CrowdControl._Trigger) -> str:
            caption = ""
            if trig.IsEnabled:
                caption = f"Enabled: '{trig.Trigger}'"
            else:
                caption = "Disabled"
            caption += "\n" + trig.Effect.Description
            return caption

        class _EffectButton(OptionBoxButton):
            TrigObj: CrowdControl._Trigger

            def __init__(self, trig: CrowdControl._Trigger) -> None:
                self.TrigObj = trig

            @property
            def Name(self) -> str:  # type: ignore
                return f"{self.TrigObj.Effect.Name}   -   {GetCaptionStr(self.TrigObj)}"

        effectButtons = [_EffectButton(trig) for trig in self.Triggers]
        currentButton = effectButtons[0]

        selectBox = OptionBox(
            Title="Configure Effects",
            Caption="Select the effect to configure.",
            Buttons=effectButtons,
            Tooltip=OptionBox.CreateTooltipString() + "     " + "[R] Reset All"
        )
        editBox = OptionBox(
            Title="Configure <effect>",
            Caption="Enabled\n<description>",
            Buttons=(
                toggleEnabledButton,
                editTriggerButton,
                extraConfigurationButton
            )
        )
        renameBox = TextInputBox(
            Title="Configure <effect>"
        )

        def UpdateEditBox() -> None:
            editBox.Title = f"Configure {currentButton.TrigObj.Effect.Name}"
            if currentButton.TrigObj.IsEnabled:
                editBox.Caption = f"Enabled: '{currentButton.TrigObj.Trigger}'"
            else:
                editBox.Caption = "Disabled"
            editBox.Caption += "\n" + currentButton.TrigObj.Effect.Description

            if currentButton.TrigObj.Effect.HasConfigMenu:
                editBox.Buttons = [toggleEnabledButton, editTriggerButton, extraConfigurationButton]
            else:
                editBox.Buttons = [toggleEnabledButton, editTriggerButton]

            editBox.Update()

        def OnSelect(button: _EffectButton) -> None:
            nonlocal currentButton
            currentButton = button
            UpdateEditBox()
            editBox.Show()

        def OnEdit(button: OptionBoxButton) -> None:
            if button == toggleEnabledButton:
                currentButton.TrigObj.IsEnabled = not currentButton.TrigObj.IsEnabled
                for option in currentButton.TrigObj.Effect.Options:
                    option.IsHidden = not currentButton.TrigObj.IsEnabled
                UpdateEditBox()
                editBox.Show()
            elif button == editTriggerButton:
                renameBox.Title = editBox.Title
                renameBox.DefaultMessage = currentButton.TrigObj.Trigger
                renameBox.Show()
            elif button == extraConfigurationButton:
                currentButton.TrigObj.Effect.FinishConfiguration = editBox.Show  # type: ignore
                currentButton.TrigObj.Effect.ShowConfiguration()

        def OnRename(msg: str) -> None:
            if len(msg) > 0:
                currentButton.TrigObj.Trigger = msg
            UpdateEditBox()
            editBox.Show()

        oldSelectInput = selectBox.OnInput

        def OnSelectInput(key: str, event: int) -> None:
            if key == "R" and event == 1:
                for trig in self.Triggers:
                    trig.IsEnabled = True
                    trig.Trigger = trig.Effect.Name
                    for option in trig.Effect.Options:
                        option.IsHidden = False
                UpdateEditBox()
                selectBox.Hide()
                selectBox.Show()
            else:
                oldSelectInput(key, event)

        selectBox.OnPress = OnSelect  # type: ignore
        selectBox.OnCancel = self.SaveTriggers  # type: ignore
        selectBox.OnInput = OnSelectInput  # type:ignore
        editBox.OnPress = OnEdit  # type: ignore
        editBox.OnCancel = lambda: selectBox.ShowButton(currentButton)  # type: ignore
        renameBox.OnSubmit = OnRename  # type: ignore
        selectBox.Show()

    def GenerateToken(self) -> None:
        continueButton = OptionBoxButton("Continue")
        yesButton = OptionBoxButton("Yes")
        noButton = OptionBoxButton("No")
        introBox = OptionBox(
            Title="Generate OAuth Token",
            Caption=(
                "If you're currently streaming, switch to an intermission screen.\n\n"
                "When you contine, a file and a website will open."
                " Login with Twitch, then copy the displayed token into the file."
                " You will be asked to confirm the token in game."
            ),
            Buttons=(continueButton,)
        )
        continueBox = OptionBox(
            Title="Generate OAuth Token",
            Caption="Continue once you've pasted the token into the file.",
            Buttons=(continueButton,)
        )
        confirmBox = OptionBox(
            Title="Generate OAuth Token",
            Caption="Is this the correct token:\n\n''",
            Buttons=(yesButton, noButton)
        )

        def ReloadToken() -> None:
            self.Token = open(self.TOKEN_FILE).read().strip()

        def OnStart(button: OptionBoxButton) -> None:
            startfile(self.TOKEN_FILE)
            webbrowser.open(self.TOKEN_URL)
            continueBox.Show()

        def OnContinue(button: OptionBoxButton) -> None:
            ReloadToken()
            confirmBox.Caption = f"Is this the correct token:\n\n'{self.Token}'"
            confirmBox.Update()
            confirmBox.Show()

        def OnConfirm(button: OptionBoxButton) -> None:
            if button == noButton:
                continueBox.Show()

        introBox.OnCancel = ReloadToken  # type: ignore
        continueBox.OnCancel = ReloadToken  # type: ignore
        confirmBox.OnCancel = ReloadToken  # type: ignore

        introBox.OnPress = OnStart  # type: ignore
        continueBox.OnPress = OnContinue  # type: ignore
        confirmBox.OnPress = OnConfirm  # type: ignore

        introBox.Show()

    def HandleChildQuit(self) -> None:
        # No need to show another message if there's already a fatal error
        if self.LatestFatalError is None:
            self.ShowFatalError("Listener program was quit.")

        self.Disable()
        self.Status = "Disabled"
        self.SettingsInputs["Enter"] = "Enable"

    def HandleStderr(self, msg: str) -> None:
        if msg.startswith("MSG: "):
            self.ShowMessage(msg[5:])
        elif msg.startswith("FTL: "):
            self.ShowFatalError(msg[5:])
        else:
            self.ShowFatalError("Unknown error:\n" + msg)

    def HandleStdout(self, msg: str) -> None:
        msg_dict: Dict[str, Any]
        title: str
        try:
            msg_dict = json.loads(msg)
            title = msg_dict["data"]["redemption"]["reward"]["title"].lower().strip()
        except (json.JSONDecodeError, KeyError) as ex:
            unrealsdk.Log("Error parsing message:")
            unrealsdk.Log(ex)
            return

        for trig in self.Triggers:
            if title == trig.Trigger.lower() and trig.IsEnabled:
                trig.Effect.OnRedeem(msg_dict)


instance = CrowdControl()
if __name__ != "__main__":
    unrealsdk.RegisterMod(instance)
else:
    unrealsdk.Log(f"[{instance.Name}] Manually loaded")
    for i in range(len(unrealsdk.Mods)):
        mod = unrealsdk.Mods[i]
        if unrealsdk.Mods[i].Name == instance.Name:
            unrealsdk.Mods[i].Disable()

            unrealsdk.RegisterMod(instance)
            unrealsdk.Mods.remove(instance)
            unrealsdk.Mods[i] = instance
            unrealsdk.Log(f"[{instance.Name}] Disabled and removed last instance")
            break
    else:
        unrealsdk.Log(f"[{instance.Name}] Could not find previous instance")
        unrealsdk.RegisterMod(instance)

    unrealsdk.Log(f"[{instance.Name}] Auto-enabling")
    instance.Status = "Enabled"
    instance.SettingsInputs["Enter"] = "Disable"
    instance.Enable()
