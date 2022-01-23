#! python3

# can't do relative import
import sys
from pathlib import PurePath

this_path = PurePath(__file__)
ext_path = this_path.parents[3]
sys.path.append(str(ext_path.parent))  # parent of the extension dir
from housingdna.extension import get_revit_info, get_model, save_json


# can't import pyrevit from cpython. yet.
# from pyrevit import forms

# no tkinter in embedded (zipped) python
# from tkinter.filedialog import asksaveasfilename

# path = asksaveasfilename(
#     title="Select filename to save",
#     initialdir=str(ext_path.parent / "housingdna/models/"),
#     initialfile="pyrevit.json",
#     defaultextension=".json",
#     filetypes=[("JSON", ".json")],
# )

r = get_revit_info(__revit__)  # type: ignore

default_name = (
    PurePath(r.doc_name if r.doc_name else "pyrevit").with_suffix(".json").name
)
model = get_model(r)

# strip null characters from pyrevit input
raw_name = input(f"Filename to save (default: {default_name})?").strip("\x00")
filename = PurePath(raw_name if raw_name else default_name).with_suffix(".json").name
print(f"Saving to {filename} ...")

save_json(model, filename)
print(model)
