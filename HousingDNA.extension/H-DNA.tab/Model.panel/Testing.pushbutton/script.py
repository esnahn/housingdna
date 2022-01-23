#! python3
# type: ignore

# can't do relative import
import sys
from pathlib import PurePath

this_path = PurePath(__file__)
ext_path = this_path.parents[3]
sys.path.append(str(ext_path.parent))  # parent of the extension dir

# can't import pyrevit from cpython. yet.

from housingdna.revitapi import (
    get_element,
    get_name,
    get_unbounded_height,
    pick_phase_by_views,
    get_boundaries,
    get_from_to_rooms,
    get_id,
    get_all_by_category,
    get_parameter_value,
    get_transparency,
)
from Autodesk.Revit import DB  # type: ignore

uidoc = __revit__.ActiveUIDocument
doc = uidoc.Document

# print(get_name(857279, doc))
# print(get_unbounded_height(857279, doc))
# print(phase := pick_phase_by_views(doc))
# print(get_name(phase, doc))
# print(get_boundaries(857279, phase, doc))
# print(get_from_to_rooms(906937, phase, doc))


def info(obj):
    try:
        print(obj, type(obj), dir(obj))
    except:
        print("pass")


# elem = get_element(408757, doc)  # k apt
# elem = get_element(485432, doc)  # sample
elem = get_element(423107, doc)  # sample entrance door
print(elem.Category.Id)
print(DB.Category.GetCategory(doc, DB.BuiltInCategory.OST_Doors).Id)
print(get_transparency(elem, doc))


print(elem.Symbol.FamilyName)
ids = elem.Symbol.GetMaterialIds(False)  # returnPaintMaterials
print(elem.Symbol.GetMaterialIds(True))  # empty

for id_ in ids:
    print(get_element(id_, doc).get_Name())
    print(get_element(id_, doc).Transparency)
    print(elem.GetMaterialArea(id_, False))
    # print(elem.GetMaterialVolume(id_))

# print(get_id(elem.Symbol))
# print(get_id(elem.GetTypeId()))

print("done")
