import unrealsdk
import argparse
from typing import Tuple

from .. import RegisterConsoleCommand
from . import obj_name_splitter, parse_object

INV_PART_CLASSES: Tuple[str, ...] = (
    "WillowInventoryPartDefinition",
    "ArtifactPartDefinition",
    "ClassModPartDefinition",
    "EquipableItemPartDefinition",
    "GrenadeModPartDefinition",
    "ItemNamePartDefinition",
    "ItemPartDefinition",
    "MissionItemPartDefinition",
    "ShieldPartDefinition",
    "UsableItemPartDefinition",
    "WeaponNamePartDefinition",
    "WeaponPartDefinition",
)

OVERRIDE_MATERIAL_CLASSES: Tuple[str, ...] = (
    "ArtifactDefinition",
    "ClassModDefinition",
    "CrossDLCClassModDefinition",
)


MESH: unrealsdk.UObject = unrealsdk.ConstructObject(
    Class="StaticMeshComponent",
    Name="CE_SetMaterial_Mesh"
)
unrealsdk.KeepAlive(MESH)


def handler(args: argparse.Namespace) -> None:
    part = parse_object(args.part)
    if part is None:
        return
    if part.Class.Name not in INV_PART_CLASSES:
        unrealsdk.Log(
            f"Object {part.PathName(part)} must be a subclass of 'WillowInventoryPartDefinition'!"
        )
        return

    template = parse_object(args.material)
    if template is None:
        return
    if template.Class.Name != "MaterialInstanceConstant":
        unrealsdk.Log(f"Object {template.PathName(template)} must be a 'MaterialInstanceConstant'!")
        return

    material = MESH.CreateAndSetMaterialInstanceConstant(0)
    unrealsdk.KeepAlive(material)

    if part.Class.Name in OVERRIDE_MATERIAL_CLASSES:
        part.OverrideMaterial = material
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
        "Sets a parts's material, without causing crashes if it's a cloned one. Practically, this"
        " creates new materials and copies the fields from the provided one as a template."
    )
)
parser.add_argument("part", help="The part to set the material on.")
parser.add_argument("material", help="The MaterialInstanceConstant to set.")
