import unrealsdk
import json
from os import path
from typing import Any, cast, ClassVar, Dict, List, Type

try:
    from Mods import AsyncUtil  # noqa  # Unused in this file but better to check in one place
    from Mods import UserFeedback

    if UserFeedback.VersionMajor < 1:
        raise RuntimeError("UserFeedback version is too old, need at least v1.3!")
    if UserFeedback.VersionMajor == 1 and UserFeedback.VersionMinor < 3:
        raise RuntimeError("UserFeedback version is too old, need at least v1.3!")
except (ImportError, RuntimeError) as ex:
    import webbrowser
    url = "https://apple1417.github.io/bl2/didntread/?m=SDK%20Autorun&au=v1.0&uf=v1.3"
    if isinstance(ex, RuntimeError):
        url += "&update"
    webbrowser.open(url)
    raise ex


from Mods.SDKAutorun import Tasks

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


class SDKAutorun(unrealsdk.BL2MOD):
    Name: ClassVar[str] = "SDK Autorun"
    Author: ClassVar[str] = "apple1417"
    Description: ClassVar[str] = (
        "Automatically runs SDK mods or console commands on game launch."
    )
    Types: ClassVar[List[unrealsdk.ModTypes]] = [unrealsdk.ModTypes.Utility]
    Version: ClassVar[str] = "1.4"

    @property
    def IsEnabled(self) -> bool:
        return self.Status == "Enabled"

    @IsEnabled.setter
    def IsEnabled(self, val: bool) -> None:
        if val:
            self.Status = "Enabled"
            self.SettingsInputs["Enter"] = "Disable"
        else:
            self.Status = "Disabled"
            self.SettingsInputs["Enter"] = "Enable"

    SettingsInputs: Dict[str, str] = {
        "Enter": "Enable",
        "T": "Edit Tasks"
    }

    CONFIG_FILE: ClassVar[str] = path.join(path.dirname(path.realpath(__file__)), "config.json")

    LaunchTasks: List[Tasks.BaseTask]
    MainMenuTasks: List[Tasks.BaseTask]

    def __init__(self) -> None:
        # Hopefully I can remove this in a future SDK update
        self.Author += "\nVersion: " + str(self.Version)  # type: ignore

        self.IsEnabled = False

        forceOff = self.LoadTasks()
        self.SaveTasks()

        if self.IsEnabled and not forceOff:
            self.Execute(self.LaunchTasks)

            def OnMainMenu(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
                self.Execute(self.MainMenuTasks)
                unrealsdk.RemoveHook("WillowGame.FrontendGFxMovie.Start", "SDKAutorun")
                return True

            unrealsdk.RegisterHook("WillowGame.FrontendGFxMovie.Start", "SDKAutorun", OnMainMenu)

    def LoadTasks(self) -> bool:
        self.LaunchTasks = []
        self.MainMenuTasks = []

        launchTasksJSON = []
        mainMenuTasksJSON = []

        try:
            with open(self.CONFIG_FILE) as file:
                loadedSettings = json.load(file)

                launchTasksJSON = loadedSettings["OnLaunch"]["Tasks"]
                mainMenuTasksJSON = loadedSettings["OnMainMenu"]["Tasks"]

                self.IsEnabled = loadedSettings["IsEnabled"]
        except FileNotFoundError:
            self.IsEnabled = False
            return True
        except (KeyError, json.JSONDecodeError):
            self.IsEnabled = False
            UserFeedback.TrainingBox(
                "SDK Autorun Error",
                "Unable to parse config file, unable to run."
            ).Show()
            return True

        anyErrors = False
        for task in launchTasksJSON:
            try:
                taskObj = Tasks.NAME_TASK_MAP[task["Type"]]()  # type: ignore
                success = taskObj.FromJSONSerializable(task["Value"])
                if not success:
                    anyErrors = True
                    continue
                self.LaunchTasks.append(taskObj)
            except KeyError:
                anyErrors = True

        for task in mainMenuTasksJSON:
            try:
                taskObj = Tasks.NAME_TASK_MAP[task["Type"]]()  # type: ignore
                success = taskObj.FromJSONSerializable(task["Value"])
                if not success:
                    anyErrors = True
                    continue
                self.MainMenuTasks.append(taskObj)
            except KeyError:
                anyErrors = True

        if anyErrors:
            UserFeedback.TrainingBox(
                "SDK Autorun Error",
                "One or more tasks was unable to be parsed and thus will be skipped."
            ).Show()
        return False

    def SaveTasks(self) -> None:
        settingsDict: Dict[str, Any] = {
            "IsEnabled": self.IsEnabled,
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
        }

        for task in self.LaunchTasks:
            settingsDict["OnLaunch"]["Tasks"].append({
                "Type": task.Name,
                "Value": task.ToJSONSerializable()
            })
        for task in self.MainMenuTasks:
            settingsDict["OnMainMenu"]["Tasks"].append({
                "Type": task.Name,
                "Value": task.ToJSONSerializable()
            })

        with open(self.CONFIG_FILE, "w") as file:
            json.dump(settingsDict, file, indent=4)

    def SettingsInputPressed(self, name: str) -> None:
        if name == "Enable":
            self.IsEnabled = True
            self.SaveTasks()
        elif name == "Disable":
            self.IsEnabled = False
            self.SaveTasks()
        elif name == "Edit Tasks":
            self.Configure()

    def Configure(self) -> None:
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

        taskButtons: List[UserFeedback.OptionBoxButton]
        if len(self.MainMenuTasks) == 0:
            # Need a dummy button to be able to create all these `OptionBox`s
            taskButtons = [UserFeedback.OptionBoxButton(
                "DUMMY", "If you can see this something has gone pretty wrong."
            )]
        else:
            taskButtons = [_TaskButton(task) for task in self.MainMenuTasks]
        taskClassButtons = [_TaskClassButton(cls) for cls in Tasks.NAME_TASK_MAP.values()]  # type: ignore
        taskClassButtons.sort(key=lambda b: b.Name)

        configureButton = UserFeedback.OptionBoxButton(
            "Configure Tasks", "View the list of all tasks, and configure them individually."
        )
        reorderButton = UserFeedback.OptionBoxButton(
            "Reorder Tasks", "Change the order in which tasks get executed."
        )
        newButton = UserFeedback.OptionBoxButton(
            "New Task", "Add a new task to the list."
        )
        deleteButton = UserFeedback.OptionBoxButton(
            "Remove Task", "Remove a task from the list."
        )

        mainButtonsNoTask = (newButton,)
        mainButtonsOneTask = (configureButton, newButton, deleteButton)
        mainButtonsNormal = (configureButton, reorderButton, newButton, deleteButton)
        mainBox = UserFeedback.OptionBox(
            Title="Edit Tasks",
            Caption="Edit the tasks that are executed upon reaching the main menu.",
            Buttons=mainButtonsNormal
        )
        if len(self.MainMenuTasks) == 0:
            mainBox.Buttons = mainButtonsNoTask
            mainBox.Update()
        elif len(self.MainMenuTasks) == 1:
            mainBox.Buttons = mainButtonsOneTask
            mainBox.Update()

        configureBox = UserFeedback.OptionBox(
            Title="Configure Tasks",
            Caption="Select the task to configure.",
            Buttons=taskButtons
        )

        reorderBox = UserFeedback.ReorderBox(
            Title="Reorder Tasks",
            Caption="Change the order in which tasks get executed.",
            Buttons=taskButtons
        )

        newBox = UserFeedback.OptionBox(
            Title="New Task",
            Caption="Select which type of task to create.",
            Buttons=taskClassButtons
        )

        deleteBox = UserFeedback.OptionBox(
            Title="Remove Task",
            Caption="Select the task to remove.",
            Buttons=taskButtons
        )

        def MainOnPress(button: UserFeedback.OptionBoxButton) -> None:
            if button == configureButton:
                configureBox.Show()
            elif button == reorderButton:
                reorderBox.Show()
            elif button == newButton:
                newBox.Show()
            elif button == deleteButton:
                deleteBox.Show()

        mainBox.OnPress = MainOnPress  # type: ignore
        mainBox.OnCancel = self.SaveTasks  # type: ignore

        def ConfigureOnPress(button: UserFeedback.OptionBoxButton) -> None:
            if not isinstance(button, _TaskButton):
                raise ValueError("Recieved button was not a task button")
            button.Task.OnFinishConfiguration = lambda: configureBox.Show(button)  # type: ignore
            button.Task.ShowConfiguration()

        configureBox.OnPress = ConfigureOnPress  # type: ignore
        configureBox.OnCancel = lambda: mainBox.Show(configureButton)  # type: ignore

        def ReorderOnExit() -> None:
            self.MainMenuTasks = [cast(_TaskButton, button).Task for button in reorderBox.Buttons]
            configureBox.Buttons = reorderBox.Buttons
            configureBox.Update()
            deleteBox.Buttons = reorderBox.Buttons
            deleteBox.Update()
            mainBox.Show(reorderButton)

        reorderBox.OnCancel = ReorderOnExit  # type: ignore

        def NewOnPress(button: UserFeedback.OptionBoxButton) -> None:
            if not isinstance(button, _TaskClassButton):
                raise ValueError("Recieved button was not a task class button")

            newTask = button.TaskClass()
            newTaskButton = _TaskButton(newTask)

            self.MainMenuTasks.append(newTask)
            # If we just added the first task
            if len(self.MainMenuTasks) == 1:
                mainBox.Buttons = mainButtonsOneTask
                mainBox.Update()
                # Remove the dummy button
                reorderBox.Buttons = []

            elif len(self.MainMenuTasks) == 2:
                mainBox.Buttons = mainButtonsNormal
                mainBox.Update()

            reorderBox.Buttons.append(newTaskButton)
            reorderBox.Update()
            configureBox.Buttons = reorderBox.Buttons
            configureBox.Update()
            deleteBox.Buttons = reorderBox.Buttons
            deleteBox.Update()

            newTask.OnFinishConfiguration = lambda: configureBox.Show(newTaskButton)  # type: ignore
            newTask.ShowConfiguration()

        newBox.OnPress = NewOnPress  # type: ignore
        newBox.OnCancel = lambda: mainBox.Show(newButton)  # type: ignore

        def DeleteOnPress(button: UserFeedback.OptionBoxButton) -> None:
            if not isinstance(button, _TaskButton):
                raise ValueError("Recieved button was not a task button")

            self.MainMenuTasks.remove(button.Task)
            reorderBox.Buttons.remove(button)
            configureBox.Buttons = reorderBox.Buttons
            deleteBox.Buttons = reorderBox.Buttons

            if len(self.MainMenuTasks) == 1:
                mainBox.Buttons = mainButtonsOneTask
                mainBox.Update()

            if len(self.MainMenuTasks) == 0:
                mainBox.Buttons = mainButtonsNoTask
                mainBox.Update()
                mainBox.Show()
            else:
                reorderBox.Update()
                configureBox.Update()
                deleteBox.Update()

                mainBox.Show(deleteButton)

        deleteBox.OnPress = DeleteOnPress  # type: ignore
        deleteBox.OnCancel = lambda: mainBox.Show(deleteButton)  # type: ignore

        mainBox.Show()

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
if __name__ != "__main__":
    unrealsdk.RegisterMod(instance)
else:
    unrealsdk.Log(f"[{instance.Name}] Manually loaded")
    for i in range(len(unrealsdk.Mods)):
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
