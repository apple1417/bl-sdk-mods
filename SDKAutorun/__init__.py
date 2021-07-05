import unrealsdk
import json
import os
from typing import Dict, List, Type, cast

from Mods.ModMenu import (EnabledSaveType, GetSettingsFilePath, LoadModSettings, Mods, ModTypes,
                          Options, RegisterMod, SaveModSettings, SDKMod)

try:
    from Mods import AsyncUtil  # noqa F401  # Unused in this file but better to check in one place
    from Mods import UserFeedback

    if UserFeedback.VersionMajor < 1:
        raise RuntimeError("UserFeedback version is too old, need at least v1.3!")
    if UserFeedback.VersionMajor == 1 and UserFeedback.VersionMinor < 3:
        raise RuntimeError("UserFeedback version is too old, need at least v1.3!")
# UF 1.0 didn't have version fields, hence the `NameError`
except (ImportError, RuntimeError, NameError) as ex:
    import webbrowser
    url = "https://apple1417.dev/bl2/didntread/?m=SDK%20Autorun&au=v1.0&uf=v1.3"
    if isinstance(ex, (RuntimeError, NameError)):
        url += "&update"
    webbrowser.open(url)
    raise ex


from . import Tasks

if __name__ == "__main__":
    import importlib
    import sys
    importlib.reload(sys.modules["Mods.AsyncUtil"])
    importlib.reload(sys.modules["Mods.UserFeedback"])
    importlib.reload(sys.modules["Mods.SDKAutorun.Tasks"])

    # See https://github.com/bl-sdk/PythonSDK/issues/68
    try:
        raise NotImplementedError
    except NotImplementedError:
        __file__ = sys.exc_info()[-1].tb_frame.f_code.co_filename  # type: ignore


class SDKAutorun(SDKMod):
    Name: str = "SDK Autorun"
    Author: str = "apple1417"
    Description: str = (
        "Automatically runs SDK mods or console commands on game launch."
    )
    Version: str = "1.5"

    Types: ModTypes = ModTypes.Utility
    SaveEnabledState: EnabledSaveType = EnabledSaveType.LoadWithSettings

    SettingsInputs: Dict[str, str] = {
        "Enter": "Enable",
        "T": "Edit Tasks"
    }

    TaskOption: Options.Hidden

    LaunchTasks: List[Tasks.BaseTask]
    MainMenuTasks: List[Tasks.BaseTask]

    def __init__(self) -> None:
        self.TaskOption = Options.Hidden("Tasks", StartingValue={
            "OnMainMenu": {
                "Tasks": []
            },
            "OnLaunch": {
                "Comment": [
                    "Congratulations, you found the secret file where you can setup tasks to run on launch.",
                    " This is not editable ingame because exec-ing mods before the main menu tends to cause",
                    " a crash, but if you really want you can edit the `Tasks` array here at your own risk."
                ],
                "Tasks": []
            }
        })
        self.Options = [self.TaskOption]
        LoadModSettings(self)

        # Load from the legacy settings file
        config_file = os.path.join(os.path.dirname(GetSettingsFilePath(self)), "config.json")
        try:
            with open(config_file) as file:
                loaded_settings = json.load(file)

                try:
                    if loaded_settings["IsEnabled"]:
                        self.SettingsInputPressed("Enable")
                except KeyError:
                    pass

                try:
                    self.TaskOption.CurrentValue["OnMainMenu"]["Tasks"] = loaded_settings["OnMainMenu"]["Tasks"]
                    self.TaskOption.CurrentValue["OnLaunch"]["Tasks"] = loaded_settings["OnLaunch"]["Tasks"]
                except KeyError:
                    pass
            SaveModSettings(self)
            os.remove(config_file)
        except json.JSONDecodeError:
            os.remove(config_file)
        except FileNotFoundError:
            pass

        self.LaunchTasks = []
        self.MainMenuTasks = []

        any_errors = False
        for task in self.TaskOption.CurrentValue["OnMainMenu"]["Tasks"]:
            try:
                task_obj = Tasks.NAME_TASK_MAP[task["Type"]]()  # type: ignore
                success = task_obj.FromJSONSerializable(task["Value"])
                if not success:
                    any_errors = True
                    continue
                self.MainMenuTasks.append(task_obj)
            except KeyError:
                any_errors = True

        for task in self.TaskOption.CurrentValue["OnLaunch"]["Tasks"]:
            try:
                task_obj = Tasks.NAME_TASK_MAP[task["Type"]]()  # type: ignore
                success = task_obj.FromJSONSerializable(task["Value"])
                if not success:
                    any_errors = True
                    continue
                self.LaunchTasks.append(task_obj)
            except KeyError:
                any_errors = True

        if any_errors:
            UserFeedback.TrainingBox(
                "SDK Autorun Error",
                "One or more tasks was unable to be parsed and thus will be skipped."
            ).Show()

        if self.IsEnabled and not any_errors:
            self.Execute(self.LaunchTasks)

            def OnMainMenu(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
                self.Execute(self.MainMenuTasks)
                unrealsdk.RemoveHook("WillowGame.FrontendGFxMovie.Start", self.Name)
                return True

            unrealsdk.RegisterHook("WillowGame.FrontendGFxMovie.Start", self.Name, OnMainMenu)

    def SettingsInputPressed(self, action: str) -> None:
        if action == "Edit Tasks":
            self.Configure()
        else:
            super().SettingsInputPressed(action)

    def Configure(self) -> None:
        def SaveTasks() -> None:
            self.TaskOption.CurrentValue["OnMainMenu"]["Tasks"] = []
            self.TaskOption.CurrentValue["OnLaunch"]["Tasks"] = []

            for task in self.MainMenuTasks:
                self.TaskOption.CurrentValue["OnMainMenu"]["Tasks"].append({
                    "Type": task.Name,
                    "Value": task.ToJSONSerializable()
                })
            for task in self.LaunchTasks:
                self.TaskOption.CurrentValue["OnLaunch"]["Tasks"].append({
                    "Type": task.Name,
                    "Value": task.ToJSONSerializable()
                })

            SaveModSettings(self)

        class _TaskButton(UserFeedback.OptionBoxButton):
            Task: Tasks.BaseTask

            @property  # type: ignore
            def Name(self) -> str:  # type: ignore
                return str(self.Task)

            @Name.setter
            def Name(self, val: str) -> None:
                pass

            def __init__(self, task: Tasks.BaseTask) -> None:
                self.Tip = task.Description
                self.Task = task

        class _TaskClassButton(UserFeedback.OptionBoxButton):
            TaskClass: Type[Tasks.BaseTask]

            def __init__(self, cls: Type[Tasks.BaseTask]) -> None:
                super().__init__(cls.Name, cls.Description)
                self.TaskClass = cls

        task_buttons: List[UserFeedback.OptionBoxButton]
        if len(self.MainMenuTasks) == 0:
            # Need a dummy button to be able to create all these `OptionBox`s
            task_buttons = [UserFeedback.OptionBoxButton(
                "DUMMY", "If you can see this something has gone pretty wrong."
            )]
        else:
            task_buttons = [_TaskButton(task) for task in self.MainMenuTasks]
        task_class_buttons = [_TaskClassButton(cls) for cls in Tasks.NAME_TASK_MAP.values()]  # type: ignore
        task_class_buttons.sort(key=lambda b: b.Name)

        configure_button = UserFeedback.OptionBoxButton(
            "Configure Tasks", "View the list of all tasks, and configure them individually."
        )
        reorder_button = UserFeedback.OptionBoxButton(
            "Reorder Tasks", "Change the order in which tasks get executed."
        )
        new_button = UserFeedback.OptionBoxButton(
            "New Task", "Add a new task to the list."
        )
        delete_button = UserFeedback.OptionBoxButton(
            "Remove Task", "Remove a task from the list."
        )

        main_buttons_no_task = (new_button,)
        main_buttons_one_task = (configure_button, new_button, delete_button)
        main_buttons_normal = (configure_button, reorder_button, new_button, delete_button)
        main_box = UserFeedback.OptionBox(
            Title="Edit Tasks",
            Caption="Edit the tasks that are executed upon reaching the main menu.",
            Buttons=main_buttons_normal
        )
        if len(self.MainMenuTasks) == 0:
            main_box.Buttons = main_buttons_no_task
            main_box.Update()
        elif len(self.MainMenuTasks) == 1:
            main_box.Buttons = main_buttons_one_task
            main_box.Update()

        configure_box = UserFeedback.OptionBox(
            Title="Configure Tasks",
            Caption="Select the task to configure.",
            Buttons=task_buttons
        )

        reorder_box = UserFeedback.ReorderBox(
            Title="Reorder Tasks",
            Caption="Change the order in which tasks get executed.",
            Buttons=task_buttons
        )

        new_box = UserFeedback.OptionBox(
            Title="New Task",
            Caption="Select which type of task to create.",
            Buttons=task_class_buttons
        )

        delete_box = UserFeedback.OptionBox(
            Title="Remove Task",
            Caption="Select the task to remove.",
            Buttons=task_buttons
        )

        def MainOnPress(button: UserFeedback.OptionBoxButton) -> None:
            if button == configure_button:
                configure_box.Show()
            elif button == reorder_button:
                reorder_box.Show()
            elif button == new_button:
                new_box.Show()
            elif button == delete_button:
                delete_box.Show()

        main_box.OnPress = MainOnPress  # type: ignore
        main_box.OnCancel = SaveTasks  # type: ignore

        def ConfigureOnPress(button: UserFeedback.OptionBoxButton) -> None:
            if not isinstance(button, _TaskButton):
                raise ValueError("Recieved button was not a task button")
            button.Task.OnFinishConfiguration = lambda: configure_box.Show(button)  # type: ignore
            button.Task.ShowConfiguration()

        configure_box.OnPress = ConfigureOnPress  # type: ignore
        configure_box.OnCancel = lambda: main_box.Show(configure_button)  # type: ignore

        def ReorderOnExit() -> None:
            self.MainMenuTasks = [cast(_TaskButton, button).Task for button in reorder_box.Buttons]
            configure_box.Buttons = reorder_box.Buttons
            configure_box.Update()
            delete_box.Buttons = reorder_box.Buttons
            delete_box.Update()
            main_box.Show(reorder_button)

        reorder_box.OnCancel = ReorderOnExit  # type: ignore

        def NewOnPress(button: UserFeedback.OptionBoxButton) -> None:
            if not isinstance(button, _TaskClassButton):
                raise ValueError("Recieved button was not a task class button")

            new_task = button.TaskClass()
            new_task_button = _TaskButton(new_task)

            self.MainMenuTasks.append(new_task)
            # If we just added the first task
            if len(self.MainMenuTasks) == 1:
                main_box.Buttons = main_buttons_one_task
                main_box.Update()
                # Remove the dummy button
                reorder_box.Buttons = []

            elif len(self.MainMenuTasks) == 2:
                main_box.Buttons = main_buttons_normal
                main_box.Update()

            reorder_box.Buttons.append(new_task_button)
            reorder_box.Update()
            configure_box.Buttons = reorder_box.Buttons
            configure_box.Update()
            delete_box.Buttons = reorder_box.Buttons
            delete_box.Update()

            new_task.OnFinishConfiguration = lambda: configure_box.Show(new_task_button)  # type: ignore
            new_task.ShowConfiguration()

        new_box.OnPress = NewOnPress  # type: ignore
        new_box.OnCancel = lambda: main_box.Show(new_button)  # type: ignore

        def DeleteOnPress(button: UserFeedback.OptionBoxButton) -> None:
            if not isinstance(button, _TaskButton):
                raise ValueError("Recieved button was not a task button")

            self.MainMenuTasks.remove(button.Task)
            reorder_box.Buttons.remove(button)
            configure_box.Buttons = reorder_box.Buttons
            delete_box.Buttons = reorder_box.Buttons

            if len(self.MainMenuTasks) == 1:
                main_box.Buttons = main_buttons_one_task
                main_box.Update()

            if len(self.MainMenuTasks) == 0:
                main_box.Buttons = main_buttons_no_task
                main_box.Update()
                main_box.Show()
            else:
                reorder_box.Update()
                configure_box.Update()
                delete_box.Update()

                main_box.Show(delete_button)

        delete_box.OnPress = DeleteOnPress  # type: ignore
        delete_box.OnCancel = lambda: main_box.Show(delete_button)  # type: ignore

        main_box.Show()

    def Execute(self, TaskList: List[Tasks.BaseTask]) -> None:
        if len(TaskList) == 0:
            return

        def OnFinish() -> None:
            unrealsdk.Log(f"[{self.Name}] Executed {len(TaskList)} tasks")

        for i in range(len(TaskList) - 1):
            TaskList[i].OnFinishExecution = TaskList[i + 1].Execute  # type: ignore
        TaskList[-1].OnFinishExecution = OnFinish  # type: ignore
        TaskList[0].Execute()


instance = SDKAutorun()
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
