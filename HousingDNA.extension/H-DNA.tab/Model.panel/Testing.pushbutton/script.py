#! python3

# can't do relative import
import sys
from pathlib import PurePath

this_path = PurePath(__file__)
ext_path = this_path.parents[3]
sys.path.append(str(ext_path.parent))  # parent of the extension dir

# can't import pyrevit from cpython. yet.
# from pyrevit import forms

import clr

clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")
clr.AddReference("AdWindows")
clr.AddReference("UIFramework")
clr.AddReference("UIFrameworkServices")

from Autodesk.Revit import DB  # type: ignore
from Autodesk.Revit.UI import UIApplication  # type: ignore

__revit__: UIApplication
assert __revit__  # type: ignore
assert isinstance(__revit__, UIApplication)

from housingdna.revitapi import (
    get_all_by_class,
    get_element,
    get_id,
    get_parameter_value,
    get_revit_doc,
    get_all_by_category,
    get_name,
    pick_phase_by_views,
)

doc = get_revit_doc(__revit__)
phase_id = pick_phase_by_views(doc)
phase = get_element(doc, phase_id)

clr_doors = get_all_by_category(doc, DB.BuiltInCategory.OST_Doors)
# print(clr_doors[2].FromRoom(phase))  # not callable
# print(clr_doors[2].FromRoom[phase])  # not subscriptable
print(clr_doors[2].get_FromRoom(phase))
