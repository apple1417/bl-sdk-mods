import importlib
import inspect
import os
import sys
from abc import ABC, abstractmethod
from types import ModuleType
from typing import Any, ClassVar, Dict, List, Union

JSON = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]


class BaseTask(ABC):
    """
    Base class to be inherited from by all tasks.

    Attributes:
        Name: The name of the task. This must be unique.
        Description:
            A short description of the task type. Displays as the tip of an `OptionsBoxButton`, and
            thus should be kept relatively short. Defaults to an empty string.
    """
    Name: ClassVar[str]
    Description: ClassVar[str] = ""

    @abstractmethod
    def Execute(self) -> None:
        """
        Function that executes whatever this task does.
        """
        raise NotImplementedError

    def OnFinishExecution(self) -> None:
        """
        Function that must be called to indicate that the task has finished executing.
        This is overwritten by the base mod during execution - don't implement it yourself.
        """
        raise NotImplementedError

    @abstractmethod
    def ShowConfiguration(self) -> None:
        """
        Shows a set of `UserFeedback` menus in order to configure the task.
        """
        raise NotImplementedError

    def OnFinishConfiguration(self) -> None:
        """
        Function that must be called to indicate that the task has finished being configured.
        This is overwritten by the base mod during configuration - don't implement it yourself.
        """
        raise NotImplementedError

    @abstractmethod
    def ToJSONSerializable(self) -> JSON:
        """
        Converts the task object into a json serializable form, to be used to save it to disk.

        Returns:
            Any object that is natively json serializable.
        """
        raise NotImplementedError

    @abstractmethod
    def FromJSONSerializable(self, data: JSON) -> bool:
        """
        Sets up the task object with json data loaded from disk - replacing any existing values.

        This *should* get passed the same data that `ToJSONSerializable` outputs.
        It is however possible that a user manually edited their config file and malformed the data.
        In this case this method should return False, and the task will be skipped over.

        Returns:
            True if given valid json data that was parsed and fully applied, False otherwise.

        """
        raise NotImplementedError

    @abstractmethod
    def __str__(self) -> str:
        """
        Converts the task object to a string (obviously), which should contain some information
        about the specific task it is configured for.

        Returns:
            The string.
        """
        raise NotImplementedError


""" A dict mapping each task name to it's class. """
NAME_TASK_MAP: Dict[str, BaseTask] = {}

_CURRENT_MODULE = "Mods.SDKAutorun.Tasks"
_dir = os.path.dirname(__file__)
for file in os.listdir(_dir):
    if not os.path.isfile(os.path.join(_dir, file)):
        continue
    if file == "__init__.py":
        continue
    name, suffix = os.path.splitext(file)
    if suffix != ".py":
        continue

    task: ModuleType
    if f"{_CURRENT_MODULE}.{name}" in sys.modules:
        task = sys.modules[f"{_CURRENT_MODULE}.{name}"]
        importlib.reload(task)
    else:
        task = importlib.import_module(f".{name}", _CURRENT_MODULE)
    # Check all classes in the file - technically you can define more than one
    for _, cls in inspect.getmembers(task, inspect.isclass):
        # Filter out classes imported from other modules
        if inspect.getmodule(cls) != task:
            continue
        # I can't use `issubclass()` because these are loaded from different files
        for c in inspect.getmro(cls)[1:]:
            if c.__name__ == BaseTask.__name__:
                NAME_TASK_MAP[cls.Name] = cls
                break
