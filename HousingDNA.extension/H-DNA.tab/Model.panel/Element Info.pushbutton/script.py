#! python3

# can't do relative import
import sys
from pathlib import PurePath

this_path = PurePath(__file__)
ext_path = this_path.parents[3]
sys.path.append(str(ext_path.parent))  # parent of the extension dir

# can't import pyrevit from cpython. yet.

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
assert isinstance(__revit__, UIApplication)  # type: ignore

from housingdna.revitapi import get_element

uidoc = __revit__.ActiveUIDocument
doc = uidoc.Document


def info(obj):
    try:
        print(obj, type(obj), dir(obj))
    except:
        print("pass")


selection = uidoc.Selection
# Autodesk.Revit.UI.Selection.Selection

selected_ids = selection.GetElementIds()
for id_ in selected_ids:
    print(int(id_.IntegerValue))
    info(get_element(doc, id_))