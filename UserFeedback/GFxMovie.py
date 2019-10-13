from abc import ABCMeta, abstractmethod


class GFxMovie(metaclass=ABCMeta):
    """
    Base class containing some of the common methods used across the various interfaces for the
     various `GFxMovie`s this library has interfaces for.
    """

    @abstractmethod
    def Show(self) -> None:
        """ Displays the movie. """
        raise NotImplementedError

    @abstractmethod
    def IsShowing(self) -> bool:
        """
        Gets if the movie is currently being displayed.

        Returns:
            True if the movie is currently being displayed, False otherwise.
        """
        raise NotImplementedError

    @abstractmethod
    def Hide(self) -> None:
        """ Hides the movie, without running any callbacks. """
        raise NotImplementedError

    # May not be the best idea to leave this here - not sure if we can get input from every movie
    def OnInput(self, key: str, event: int) -> None:
        """
        Callback function intended to be overwritten. Called any time the user inputs anything while
         the movie is open.

        Args:
            key:
                The key that was pressed. See the following link for reference.
                https://api.unrealengine.com/udk/Three/KeyBinds.html#Mappable%20keys
            event:
                The input event type. See the following link for reference.
                https://docs.unrealengine.com/en-US/API/Runtime/Engine/Engine/EInputEvent/index.html
        """
        pass
