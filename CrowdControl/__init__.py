import unrealsdk
import json
import msvcrt
import subprocess
import sys
import webbrowser
from dataclasses import dataclass
from os import path, startfile
from typing import Any, ClassVar, Dict, IO, List, Optional

from Mods.ModMenu import EnabledSaveType, Mods, ModTypes, Options, RegisterMod, SDKMod
from Mods.CrowdControl import Effects

try:
    from Mods import AsyncUtil
    from Mods import UserFeedback
    from Mods.UserFeedback import ShowHUDMessage, OptionBox, OptionBoxButton, TextInputBox, TrainingBox

    if UserFeedback.VersionMajor < 1:
        raise RuntimeError("UserFeedback version is too old, need at least v1.3!")
    if UserFeedback.VersionMajor == 1 and UserFeedback.VersionMinor < 3:
        raise RuntimeError("UserFeedback version is too old, need at least v1.3!")
# UF 1.0 didn't have version fields, hence the `NameError`
except (ImportError, RuntimeError, NameError) as ex:
    url = "https://apple1417.github.io/bl2/didntread/?m=Borderlands%20Crowd%20Control&au=v1.0&uf=v1.3"
    if isinstance(ex, (RuntimeError, NameError)):
        url += "&update"
    webbrowser.open(url)
    raise ex

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

from ctypes import byref, GetLastError, windll, WinError  # noqa E402
from ctypes.wintypes import BYTE, DWORD  # noqa E402

ERROR_BROKEN_PIPE = 109
STARTF_USESHOWWINDOW = 1
SW_SHOWMINNOACTIVE = 7


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
        if GetLastError() == ERROR_BROKEN_PIPE:
            return 0
        raise WinError()

    return available.value


class CrowdControl(SDKMod):
    Name: str = "Borderlands Crowd Control"
    Author: str = "apple1417"
    Description: str = (
        "<font size='24' color='#FFDEAD'></font>\n"
        "Lets viewers on Twitch spend channel points to affect your game."
    )
    Version: str = "1.3"

    Types: ModTypes = ModTypes.Utility | ModTypes.Gameplay
    # I'd rather not launch the listener with the game, best to be explicit
    SaveEnabledState: EnabledSaveType = EnabledSaveType.NotSaved

    SettingsInputs: Dict[str, str]
    Options: List[Options.Base]

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

    def SettingsInputPressed(self, action: str) -> None:
        if action == "Enable" and self.Token is not None:
            if not self.IsEnabled:
                self.Enable()
                self.IsEnabled = True
            self.Status = "Enabled"
            self.SettingsInputs["Enter"] = "Disable"
        elif action == "Disable":
            if self.IsEnabled:
                self.Disable()
                self.IsEnabled = False
            self.Status = "Disabled"
            self.SettingsInputs["Enter"] = "Enable"

        elif action == "Configure Effects":
            self.Configure()
        elif action == "Generate Token":
            self.GenerateToken()

    def Enable(self) -> None:
        if self.Token is None:
            return

        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = SW_SHOWMINNOACTIVE

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
                if self._listener.stderr is not None:
                    line = self._listener.stderr.read()
                    if len(line) > 0:
                        self.HandleStderr(line.decode("utf8").replace("\\n", "\n")[:-2])
                self.HandleChildQuit()
                return

            if self._listener.stdout is not None:
                if GetPipeAvailableLen(self._listener.stdout) > 0:
                    line = self._listener.stdout.readline()
                    self.HandleStdout(line.decode("utf8").replace("\\n", "\n")[:-2])

            if self._listener.stderr is not None:
                if GetPipeAvailableLen(self._listener.stderr) > 0:
                    line = self._listener.stderr.readline()
                    self.HandleStderr(line.decode("utf8").replace("\\n", "\n")[:-2])

        def OnQuit(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if self._listener is not None:
                self._listener.kill()

            return True

        AsyncUtil.RunEveryTick(OnTick, "CrowdControl")

        # TODO: better quit hook
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
        toggle_enabled_button = OptionBoxButton("Toggle Enabled")
        edit_trigger_button = OptionBoxButton(
            "Edit Trigger",
            "Edits what redemption title triggers this effect. Not case sensitive, but must match exactly otherwise."
        )
        extra_configuration_button = OptionBoxButton(
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

        effect_buttons = [_EffectButton(trig) for trig in self.Triggers]
        current_button = effect_buttons[0]

        select_box = OptionBox(
            Title="Configure Effects",
            Caption="Select the effect to configure.",
            Buttons=effect_buttons,
            Tooltip=OptionBox.CreateTooltipString() + "     " + "[R] Reset All"
        )
        edit_box = OptionBox(
            Title="Configure <effect>",
            Caption="Enabled\n<description>",
            Buttons=(
                toggle_enabled_button,
                edit_trigger_button,
                extra_configuration_button
            )
        )
        rename_box = TextInputBox(
            Title="Configure <effect>"
        )

        def UpdateEditBox() -> None:
            edit_box.Title = f"Configure {current_button.TrigObj.Effect.Name}"
            if current_button.TrigObj.IsEnabled:
                edit_box.Caption = f"Enabled: '{current_button.TrigObj.Trigger}'"
            else:
                edit_box.Caption = "Disabled"
            edit_box.Caption += "\n" + current_button.TrigObj.Effect.Description

            if current_button.TrigObj.Effect.HasConfigMenu:
                edit_box.Buttons = [toggle_enabled_button, edit_trigger_button, extra_configuration_button]
            else:
                edit_box.Buttons = [toggle_enabled_button, edit_trigger_button]

            edit_box.Update()

        def OnSelect(button: _EffectButton) -> None:
            nonlocal current_button
            current_button = button
            UpdateEditBox()
            edit_box.Show()

        def OnEdit(button: OptionBoxButton) -> None:
            if button == toggle_enabled_button:
                current_button.TrigObj.IsEnabled = not current_button.TrigObj.IsEnabled
                for option in current_button.TrigObj.Effect.Options:
                    option.IsHidden = not current_button.TrigObj.IsEnabled
                UpdateEditBox()
                edit_box.Show()
            elif button == edit_trigger_button:
                rename_box.Title = edit_box.Title
                rename_box.DefaultMessage = current_button.TrigObj.Trigger
                rename_box.Show()
            elif button == extra_configuration_button:
                current_button.TrigObj.Effect.FinishConfiguration = edit_box.Show  # type: ignore
                current_button.TrigObj.Effect.ShowConfiguration()

        def OnRename(msg: str) -> None:
            if len(msg) > 0:
                current_button.TrigObj.Trigger = msg
            UpdateEditBox()
            edit_box.Show()

        old_select_input = select_box.OnInput

        def OnSelectInput(key: str, event: int) -> None:
            if key == "R" and event == 1:
                for trig in self.Triggers:
                    trig.IsEnabled = True
                    trig.Trigger = trig.Effect.Name
                    for option in trig.Effect.Options:
                        option.IsHidden = False
                UpdateEditBox()
                select_box.Hide()
                select_box.Show()
            else:
                old_select_input(key, event)

        select_box.OnPress = OnSelect  # type: ignore
        select_box.OnCancel = self.SaveTriggers  # type: ignore
        select_box.OnInput = OnSelectInput  # type:ignore
        edit_box.OnPress = OnEdit  # type: ignore
        edit_box.OnCancel = lambda: select_box.Show(current_button)  # type: ignore
        rename_box.OnSubmit = OnRename  # type: ignore
        select_box.Show()

    def GenerateToken(self) -> None:
        continue_button = OptionBoxButton("Continue")
        yes_button = OptionBoxButton("Yes")
        no_button = OptionBoxButton("No")
        intro_box = OptionBox(
            Title="Generate OAuth Token",
            Caption=(
                "If you're currently streaming, switch to an intermission screen.\n\n"
                "When you contine, a file and a website will open."
                " Login with Twitch, then copy the displayed token into the file."
                " You will be asked to confirm the token in game."
            ),
            Buttons=(continue_button,)
        )
        continue_box = OptionBox(
            Title="Generate OAuth Token",
            Caption="Continue once you've pasted the token into the file.",
            Buttons=(continue_button,)
        )
        confirm_box = OptionBox(
            Title="Generate OAuth Token",
            Caption="Is this the correct token:\n\n''",
            Buttons=(yes_button, no_button)
        )

        def ReloadToken() -> None:
            self.Token = open(self.TOKEN_FILE).read().strip()

        def OnStart(button: OptionBoxButton) -> None:
            startfile(self.TOKEN_FILE)
            webbrowser.open(self.TOKEN_URL)
            continue_box.Show()

        def OnContinue(button: OptionBoxButton) -> None:
            ReloadToken()
            confirm_box.Caption = f"Is this the correct token:\n\n'{self.Token}'"
            confirm_box.Update()
            confirm_box.Show()

        def OnConfirm(button: OptionBoxButton) -> None:
            if button == no_button:
                continue_box.Show()

        intro_box.OnCancel = ReloadToken  # type: ignore
        continue_box.OnCancel = ReloadToken  # type: ignore
        confirm_box.OnCancel = ReloadToken  # type: ignore

        intro_box.OnPress = OnStart  # type: ignore
        continue_box.OnPress = OnContinue  # type: ignore
        confirm_box.OnPress = OnConfirm  # type: ignore

        intro_box.Show()

    def HandleChildQuit(self) -> None:
        # No need to show another message if there's already a fatal error
        if self.LatestFatalError is None:
            self.ShowFatalError("Listener program was quit.")

        self.SettingsInputPressed("Disable")

    def HandleStderr(self, msg: str) -> None:
        if msg.startswith("MSG: "):
            self.ShowMessage(msg[5:])
        elif msg.startswith("FTL: "):
            self.ShowFatalError(msg[5:])
            self.SettingsInputPressed("Disable")
        else:
            self.ShowFatalError("Unknown error:\n" + msg)
            self.SettingsInputPressed("Disable")

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
if __name__ == "__main__":
    unrealsdk.Log(f"[{instance.Name}] Manually loaded")
    for mod in Mods:
        if mod.Name == instance.Name:
            if mod.IsEnabled:
                mod.Disable()
            Mods.remove(mod)
            unrealsdk.Log(f"[{instance.Name}] Removed last instance")

            # Fixes inspect.getfile()
            instance.__class__.__module__ = mod.__class__.__module__
            break
RegisterMod(instance)
