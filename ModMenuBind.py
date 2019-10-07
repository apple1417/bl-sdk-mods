import bl2sdk


def HookMainMenuInput(caller: bl2sdk.UObject, function: bl2sdk.UFunction, params: bl2sdk.FStruct) -> bool:
    if params.ukey == "M":
        caller.ShowMarketplaceMovie()
    return True


bl2sdk.RemoveHook("WillowGame.FrontendGFxMovie.SharedHandleInputKey", "ModMenuBind")
bl2sdk.RegisterHook("WillowGame.FrontendGFxMovie.SharedHandleInputKey", "ModMenuBind", HookMainMenuInput)
