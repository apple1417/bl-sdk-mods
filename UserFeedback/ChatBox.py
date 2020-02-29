import unrealsdk
from .GFxMovie import GFxMovie

"""
This class is not reccomended to be used.

There to various bugs out of my control, depending on implementation you either confuse the game
 about what `GFxMovie` is focused, softlocking you until you run the command `disconnect`, or just
 plain crash the game.

This file has only been left in so that the code isn't lost - if it can be made to work then this
 would be a much more elegant alternative to `TextInputBox`.
"""

_ChatDef = unrealsdk.FindObject("GFxMovieDefinition", "UI_TextChat.TextChat_Def")


class ChatBox(GFxMovie):
    """
    Class representing a chat box, allowing you to get text input.

    This intercepts the chat output, nothing actually gets said.

    Note that for some reason creating too many of these can mess with what `GFxMovie` the game
     considers to be focused. This means the user might end up controlling a movie they can't see
     because it's hidden under others.
    It seems to be because the game objects this class uses (1 per instance) don't get GCed until
     the level changes. You should be able to reuse the same instance realtivly easily anyway.

    Attributes:
        Priority:
            A byte representing the priority of the chat box in reference to the game's other
             `GfxMovie`s. Higher values display above lower ones.
    """

    Priority: int

    # This var is not neccesarily accurate, you should still call IsShowing()
    _WasChatOpened: bool
    _Chat: unrealsdk.UObject

    def __init__(
        self,
        Priority: int = 250
    ) -> None:
        """
        Creates the chat box.

        Args:
            Priority:
                A byte representing the priority of the chat box in reference to the game's other
                 `GfxMovie`s. Higher values display above lower ones. Defaults to 250, the same as
                 the game's default.

        """
        self.Priority = Priority

        self._WasChatOpened = False

        self._Chat = unrealsdk.GetEngine().GamePlayers[0].Actor.GFxUIManager.PlayMovie(_ChatDef)
        self._Chat.StopTextChatInternal()
        self._Chat.Close()

    def _IsChatGCed(self) -> bool:
        """
        Returns if our chat object has been Garbage Collected.

        We want to keep the same chat object around as long as possible, because as explained above
         for some reason using too many messes with `GFxMovie` focus. This means we need to know
         when our object has been GCed.

        Now you might just say "Use unrealsdk.KeepAlive()", but that does not actually stop it from
         being unloaded - presumably because it's in `Transient`.

        Unfortuantly, the SDK doesn't provide a proper way to check this if an object is GCed, best
         we have is checking if the string representation returns `(null)`, and if fields that
         should never be None have been set to that.

        Even more unfortuantly, despite all my best efforts to find a workaround, the game can still
         crash when you try access a GCed object. This is why this class is not recommended to be
         used yet.
        """
        return str(self._Chat) == "(null)" or self._Chat.DelayUntilShowOk is None

    def Show(self) -> None:
        """ Displays the chat box. """
        if self._IsChatGCed():
            self._Chat = unrealsdk.GetEngine().GamePlayers[0].Actor.GFxUIManager.PlayMovie(_ChatDef)

        self._Chat.SetPriority(self.Priority)
        self._Chat.StartTextChat()
        self._WasChatOpened = True

        def AddChatMessageInternal(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            # Oddly enough it tries to call this on the object for the actual chatbox, not our own
            #  one, so we have to block it on all objects - likely won't matter but worth noting.
            unrealsdk.RemoveHook("WillowGame.TextChatGFxMovie.AddChatMessageInternal", "ChatBoxInput")
            unrealsdk.RemoveHook("WillowGame.TextChatGFxMovie.HandleTextChatInput", "ChatBoxInput")
            self.OnSubmit(params.msg)
            return False

        def HandleTextChatInput(caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
            if caller == self._Chat:
                self.OnInput(params.ukey, params.uevent)
                if params.ukey == "Escape":
                    unrealsdk.RemoveHook("WillowGame.TextChatGFxMovie.AddChatMessageInternal", "ChatBoxInput")
                    unrealsdk.RemoveHook("WillowGame.TextChatGFxMovie.HandleTextChatInput", "ChatBoxInput")
                    self.OnSubmit("")
            return True

        unrealsdk.RegisterHook("WillowGame.TextChatGFxMovie.AddChatMessageInternal", "ChatBoxInput", AddChatMessageInternal)
        unrealsdk.RegisterHook("WillowGame.TextChatGFxMovie.HandleTextChatInput", "ChatBoxInput", HandleTextChatInput)

    def IsShowing(self) -> bool:
        """
        Gets if the chat box is currently being displayed.

        Returns:
            True if the chat box is currently being displayed, False otherwise.
        """
        if self._IsChatGCed() and self._WasChatOpened:
            self._WasChatOpened = False
            # If we thought chat was open then we likely still have hooks lying around
            unrealsdk.RemoveHook("WillowGame.TextChatGFxMovie.AddChatMessageInternal", "ChatBoxInput")
            unrealsdk.RemoveHook("WillowGame.TextChatGFxMovie.HandleTextChatInput", "ChatBoxInput")

        return self._WasChatOpened

    def Hide(self) -> None:
        """
        Hides the chat box, without running any callbacks.

        Displays a warning but does nothing if the chat box is not currently being displayed.
        """
        if not self.IsShowing():
            unrealsdk.Log("[UserFeedback] Warning: tried to hide a chat box that was already closed")
            return

        unrealsdk.RemoveHook("WillowGame.TextChatGFxMovie.AddChatMessageInternal", "ChatBoxInput")
        unrealsdk.RemoveHook("WillowGame.TextChatGFxMovie.HandleTextChatInput", "ChatBoxInput")

        self._Chat.StopTextChatInternal()
        self._Chat.Close()

    def OnSubmit(self, msg: str) -> None:
        """
        Callback function intended to be overwritten. Called when the user presses enter to submit
         their message.

        Args:
            msg: The message the user wrote. Note that this may be the empty string.
        """
        pass
