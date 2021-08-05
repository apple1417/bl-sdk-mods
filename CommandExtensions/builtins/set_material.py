import unrealsdk
import argparse
from typing import Tuple

from Mods.ModMenu.DeprecationHelper import Deprecated

from .. import RegisterConsoleCommand
from . import is_obj_instance, obj_name_splitter, parse_object

OVERRIDE_MATERIAL_CLASSES: Tuple[str, ...] = (
    "ArtifactDefinition",
    "ClassModDefinition",
)


MESH: unrealsdk.UObject = unrealsdk.ConstructObject(
    Class="StaticMeshComponent",
    Name="CE_SetMaterial_Mesh"
)
unrealsdk.KeepAlive(MESH)


@Deprecated(
    "`set_material` is deprecated, clone `Engine.Default__MaterialInstanceConstant` instead"
)
def handler(args: argparse.Namespace) -> None:
    part = parse_object(args.part)
    if part is None:
        return
    if not is_obj_instance(part, "WillowInventoryPartDefinition"):
        unrealsdk.Log(
            f"Object {part.PathName(part)} must be a subclass of 'WillowInventoryPartDefinition'!"
        )
        return

    template = parse_object(args.material)
    if template is None:
        return
    if not is_obj_instance(template, "MaterialInstanceConstant"):
        unrealsdk.Log(f"Object {template.PathName(template)} must be a 'MaterialInstanceConstant'!")
        return

    material = MESH.CreateAndSetMaterialInstanceConstant(0)
    unrealsdk.KeepAlive(material)

    for cls in OVERRIDE_MATERIAL_CLASSES:
        if is_obj_instance(part, cls):
            part.OverrideMaterial = material
            break
    else:
        part.Material = material

    material.ClearParameterValues()
    for val in template.FontParameterValues:
        material.SetFontParameterValue(val.ParameterName, val.FontValue, val.FontPage)
    for val in template.ScalarParameterValues:
        material.SetScalarParameterValue(val.ParameterName, val.ParameterValue)
    for val in template.TextureParameterValues:
        material.SetTextureParameterValue(val.ParameterName, val.ParameterValue)
    for val in template.VectorParameterValues:
        material.SetVectorParameterValue(val.ParameterName, (
            val.ParameterValue.R,
            val.ParameterValue.G,
            val.ParameterValue.B,
            val.ParameterValue.A
        ))
    material.SetParent(template.Parent)


parser = RegisterConsoleCommand(
    "set_material",
    handler,
    splitter=obj_name_splitter,
    description=(
        "DEPRECATED. "
        "Sets a parts's material, without causing crashes if it's a cloned from an existing one."
        " Note that cloning `Engine.Default__MaterialInstanceConstant` will not cause crashes, this"
        " command is most useful when only making a small edit. Practically, this creates a new"
        " material and copies the fields from the provided one as a template."
    )
)
parser.add_argument("part", help="The part to set the material on.")
parser.add_argument("material", help="The MaterialInstanceConstant to set.")
