#! python3
# type: ignore

# can't do relative import
import sys
from pathlib import PurePath
from typing import Sequence, Tuple


this_path = PurePath(__file__)
ext_path = this_path.parents[3]
sys.path.append(str(ext_path.parent))  # parent of the extension dir

# can't import pyrevit from cpython. yet.
# from pyrevit import forms
# from pyrevit import HOST_APP, EXEC_PARAMS
# from pyrevit import revit

import clr

clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")
clr.AddReference("AdWindows")
clr.AddReference("UIFramework")
clr.AddReference("UIFrameworkServices")

from System import Enum
from Autodesk.Revit import DB
from Autodesk.Revit.UI import UIApplication

__revit__: UIApplication
assert isinstance(__revit__, UIApplication)

from housingdna.model import Direction
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
import math
from pprint import pprint

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
    break
elem = get_element(doc, id_)

# elem = get_element(doc, DB.ElementId(457534))
# info(elem)  # 457534
# 침실 204 도남/진남동 방향 창

### category

# info(elem.Category.Name)  # 창
# print(elem.Category.Id.IntegerValue)  # -2000014
# info(Enum.GetName(DB.BuiltInCategory, -2000014))  # OST_Windows

# clr_windows = get_all_by_category(doc, -2000014)
# print(window_ids := [get_id(x) for x in clr_windows])
# print(457534 in window_ids)  # True

# print(clr_windows[0].HasModifiedGeometry())  # False
# print(clr_windows[0].GetFamilyPointPlacementReferences())  # []

# opt = DB.Options()
# info(geo := elem.GetOriginalGeometry(opt))  # GeometryElement
# [info(x) for x in geo]  # 6 solids

# print(clr_windows[0].Geometry)  # no attr

# print(clr_windows[0].GetSpatialElementCalculationPoint())  # error
# print(
#     clr_windows[0].GetSpatialElementFromToCalculationPoints()
# )  # This instance does not have from/to calculation points.

# t = elem.GetTransform()  # Transform
# # t = elem.GetTotalTransform()  # Transform
# print(t.BasisX)  # (-1.000000000, 0.000000000, 0.000000000)
# print(t.BasisY)  # (0.000000000, -1.000000000, 0.000000000)
# print(t.BasisZ)  # (0.000000000, 0.000000000, 1.000000000)
# print(t.Determinant)  # 1.0

# print(elem.HandOrientation)  # XYZ(-1, 0, 0)
# print(elem.HandFlipped)  # False

# print(elem.FacingOrientation)  # XYZ(0, -1, 0)
# print(elem.FacingFlipped)  # False

# print(elem.Mirrored)  # False

phase = pick_phase_by_views(doc)
clr_phase = get_element(doc, phase)

print(fromroom := elem.get_FromRoom(clr_phase))  # Room
print(toroom := elem.get_ToRoom(clr_phase))  # None
print(elem.LevelId)  # 245423

print(elem.Location)  # LocationPoint
print(loc := elem.Location.Point)  # XYZ(10.865917052, -10.835282082, 9.842519685)
print(rot := elem.Location.Rotation)  # 3.14159265358979

print(facing := elem.FacingOrientation)  # XYZ(0, -1, 0)
print(elem.FacingFlipped)  # False

# print(elem.HasModifiedGeometry())  # False
# print(elem.HasSweptProfile())  # False

# info(elem.Host)  # Wall
# print(elem.HostFace)  # None
# print(elem.HostParameter)  # 41.83...

# print(elem.get_Room(clr_phase))  # None
# print(elem.get_Space(clr_phase))  # None
# print(elem.SuperComponent)  # None

# print(elem.BoundingBox)  # no attr
# print(elem.Split(0.5))  # cannot be split

boundary_opt = DB.SpatialElementBoundaryOptions()
boundary_opt.SpatialElementBoundaryLocation = DB.SpatialElementBoundaryLocation.Finish
boundary_opt.StoreFreeBoundaryFaces = True

if fromroom:
    seglistlist = fromroom.GetBoundarySegments(boundary_opt)
elif toroom:
    seglistlist = toroom.GetBoundarySegments(boundary_opt)
else:
    raise

# donut = get_element(doc, DB.ElementId(1105835))
# seglistlist = donut.GetBoundarySegments(boundary_opt)


def eval_curve(
    curve: DB.Curve, first=False, division=8
) -> Sequence[Tuple[float, float]]:
    points = []

    if curve.IsBound:
        param_start = curve.GetEndParameter(0)
        param_end = curve.GetEndParameter(1)
    elif isinstance(curve, (DB.Arc, DB.Ellipse)):  # unbound arc: circle or ellipse
        param_start = 0
        param_end = 2 * math.pi
    else:
        raise  # no unbound spline, or etc.

    d_param = (param_end - param_start) / division

    for i in range(0 if first else 1, division + 1):
        point = curve.Evaluate(param_start + i * d_param, False)
        points.append((point.X, point.Y))

    return points


def get_2d_points(
    curve: DB.Curve, first=False, division=8
) -> Sequence[Tuple[float, float]]:
    if isinstance(curve, DB.Line):
        if curve.IsBound:
            points = []

            for i in [0, 1] if first else [1]:
                point = curve.GetEndPoint(i)
                points.append((point.X, point.Y))

            return points
        else:
            raise  # no unbound line
    else:
        return eval_curve(curve, first, division)


rings = []

for seglist in seglistlist:
    print("new ring")

    ring = []
    first = True

    for seg in seglist:

        curve = seg.GetCurve()
        ring.extend(get_2d_points(curve, first))

        first = False

    rings.append(ring)

# pprint(rings)
shell = rings[0]
holes = rings[1:]

import numpy as np
from shapely.geometry import Polygon, Point
from shapely.geometry.geo import box
from shapely.ops import nearest_points

room = Polygon(shell, holes)
pprint(room.area)
window = Point(loc.X, loc.Y)
# pprint(nearest_points(room, window)[0].wkt)
window_box = box(window.x - 1, window.y - 1, window.x + 1, window.y + 1)
x = window_box.intersection(room)
c = x.centroid
pprint(c.wkt)
pprint((window.x - c.x, window.y - c.y))


def azimuth(point1: Point, point2: Point):
    """azimuth between 2 shapely points in radian 0 to 2pi.

    https://gis.stackexchange.com/questions/200971/angle-at-intersection-point-from-two-lines
    """
    angle = np.arctan2(point2.x - point1.x, point2.y - point1.y)
    return angle if angle >= 0 else angle + 2 * math.pi


# print(azimuth(Point(0, 0), Point(0, 1)))  # north == 0
# print(azimuth(Point(0, 0), Point(1, 0)))  # east == 1/2*pi
# print(azimuth(Point(0, 0), Point(0, -1)))  # south == pi
# print(azimuth(Point(0, 0), Point(-1, 0)))  # west == 3/2*pi
print(azimuth(c, window))  # azimuth from centroid to window: pi == south

pl = doc.ActiveProjectLocation
pp = pl.GetProjectPosition(DB.XYZ.Zero)
print(pp.Angle)  # 0.64 from -pi to pi

# the window is in true southeast. (small in azimuth)
# angle difference between project north and true north should be subtracted.

print(azimuth(c, window) - pp.Angle)
print(
    Direction(
        round((((azimuth(c, window) - pp.Angle) / (2 * math.pi)) + 100) * 8) % 8 + 1
    )
)
