# Export everything from the other files
from .GFxMovie import GFxMovie as GFxMovie
from .Misc import ShowHUDMessage as ShowHUDMessage
from .Misc import ShowChatMessage as ShowChatMessage
from .OptionBox import OptionBox as OptionBox
from .OptionBox import OptionBoxButton as OptionBoxButton
from .TextInputBox import TextInputBox as TextInputBox
from .TrainingBox import TrainingBox as TrainingBox

VersionMajor: int = 1
VersionMinor: int = 2

# Just to satisfy pyflakes' unused imports warning - can't seem to get it to ignore this file
if False:
    GFxMovie()
    ShowHUDMessage()
    ShowChatMessage()
    OptionBox()
    OptionBoxButton()
    TextInputBox()
    TrainingBox()
