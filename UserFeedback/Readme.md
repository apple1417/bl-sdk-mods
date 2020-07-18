## Changelog

### User Feedback v1.4
Removed the `unsafe_hash = True` tag from `OptionsBoxButton`. This is a breaking change, but putting these objects in a dict was very precarious to begin with.    

### User Feedback v1.3
Added an entry in the Mods list, so that users can see their version and verify that it's loaded.    
Added `ReorderBox`, a subclass of `OptionBox` designed around reordering it's buttons.

##### OptionBox
Added a `ScrollType` field, taking a value from the new `OptionScrollType` enum. Defines various different ways of scrolling between pages.    
Changed default scroll type to `UNIDIRECTIONAL_HOVER` rather than `UNIDIRECTIONAL`, which the old behaviour was equivalent to.    
Swapped the default binds of `PageUp` and `PageDown` to be more intuitive.    
Moved the code handling `PageUp`/`PageDown`/`Home`/`End` inputs to an internal callback, so you can directly overwrite `OnInput` but keep their behaviour.    
Moved various internal callbacks to class rather than local functions, meaning subclasses can more easily overwrite them.    
Fixed that having an invalid amount of buttons would never raise `ValueError`s.    
Deprecated `ShowButton` in favour of an optional argument on `Show`.

##### TextInputBox
Added `IsAllowedToWrite` allowing for advanced input filtering.

##### TrainingBox
Fixed that `IsShowing` returned inverted results.
Fixed that hiding the dialog from within `OnInput` would raise `AttributeError`s.

### User Feedback v1.2
Added `ShowChatMessage`.    
Made `OptionsBoxButton` into a dataclass.

### User Feedback v1.1
Updated for SDK versions 0.7.4-0.7.6.    
Added `VersionMajor` and `VersionMinor` fields to the package.

### User Feedback v1.0
Inital Release.
