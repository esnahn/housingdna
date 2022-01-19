#! python3
# type: ignore

# can't do relative import
from operator import le
import sys
from pathlib import PurePath
from typing import Sequence, Tuple, Union

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

from housingdna.model import Direction, RoomOpeningRelation
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
import itertools

uidoc = __revit__.ActiveUIDocument
doc = uidoc.Document


def info(obj):
    try:
        print(obj, type(obj), dir(obj))
    except:
        print("pass")


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


def get_points_2d(
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


def get_boundary_2d(
    elem: Union[int, DB.ElementId, DB.SpatialElement], division=8
) -> Sequence[Sequence[Tuple[float, float]]]:
    if isinstance(elem, (int, DB.ElementId)):
        elem = get_element(elem)

    boundary_opt = DB.SpatialElementBoundaryOptions()
    boundary_opt.SpatialElementBoundaryLocation = (
        DB.SpatialElementBoundaryLocation.Center
    )
    boundary_opt.StoreFreeBoundaryFaces = True

    seglistlist = elem.GetBoundarySegments(boundary_opt)

    rings = []
    for seglist in seglistlist:
        first = True

        ring = []
        for seg in seglist:
            curve = seg.GetCurve()
            ring.extend(get_points_2d(curve, first, division))

            first = False

        rings.append(ring)

    return rings


# elem = get_element(doc, DB.ElementId(413691))
# info(elem.WallType.Kind)
# print(DB.WallKind.Curtain)

# elem_ids = [get_id(elem)]
# curve = elem.Location.Curve
# line = get_points_2d(curve)
# print(line)


clr_sep_lines = get_all_by_category(doc, DB.BuiltInCategory.OST_RoomSeparationLines)

curtain_walls = []
curtain_wall_shapes = {}
for wall in clr_sep_lines:
    id_ = get_id(wall)

    curtain_walls.append(id_)

    curtain_wall_shapes[id_] = get_points_2d(wall.Location.Curve, first=True)

# pprint(curtain_wall_shapes, width=len(str(curtain_wall_shapes)) // 2)
# pprint(curtain_wall_shapes, depth=2)

clr_rooms = get_all_by_category(doc, DB.BuiltInCategory.OST_Rooms)

boundary_opt = DB.SpatialElementBoundaryOptions()
boundary_opt.SpatialElementBoundaryLocation = DB.SpatialElementBoundaryLocation.Center
boundary_opt.StoreFreeBoundaryFaces = True

rel_rooms = {}
for room in clr_rooms:
    room_id = get_id(room)
    seglistlist = room.GetBoundarySegments(boundary_opt)
    for seg in itertools.chain.from_iterable(seglistlist):
        # Retrieve the id of the element that produces this boundary segment.
        # https://www.revitapidocs.com/2022/eaf7d628-d9c2-80a3-2fd7-00013bab1377.htm
        id_ = seg.ElementId.IntegerValue
        if id_ in curtain_walls:
            rel_rooms.setdefault(id_, set()).add(room_id)

print(rel_rooms)

boundaries = {get_id(room): get_boundary_2d(room) for room in clr_rooms}
# pprint(boundaries, width=len(str(boundaries)) // 2)
# pprint(boundaries, depth=2)

import numpy as np
from shapely.geometry import Polygon, Point, LineString
from shapely.geometry.geo import box
from shapely.ops import nearest_points

room_shapes = {
    id_: Polygon(rings[0], rings[1:]) for id_, rings in boundaries.items() if rings
}
# pprint(room_shapes, depth=2)


def azimuth(point1: Union[Point, Tuple], point2: Union[Point, Tuple]):
    """azimuth between 2 shapely points in radian 0 to 2pi.

    https://gis.stackexchange.com/questions/200971/angle-at-intersection-point-from-two-lines
    """
    if isinstance(point1, Point):
        x1, y1 = point1.x, point1.y
    else:
        x1, y1 = point1
    if isinstance(point2, Point):
        x2, y2 = point2.x, point2.y
    else:
        x2, y2 = point2

    angle = np.arctan2(x2 - x1, y2 - y1)
    return angle if angle >= 0 else angle + 2 * math.pi


pl = doc.ActiveProjectLocation
pp = pl.GetProjectPosition(DB.XYZ.Zero)
print(pp.Angle)  # 0.64 from -pi to pi

room_opening_relations = []
for wall, rooms in rel_rooms.items():
    # per wall
    # print(wall)
    wall_points = curtain_wall_shapes[wall]

    # list of bearing, line pairs
    wall_segments: Sequence[Tuple[Direction, LineString]] = []
    for i, point in enumerate(wall_points):
        if i == 0:  # at the start
            first_i = i
            continue
        # assuming the room is left side of advance
        # + pi/2 to rotate 90 deg clockwise in azimuth
        bearing_from_left = (
            azimuth(wall_points[i - 1], point)  # from last point
            + (math.pi / 2)  # rotate 90 deg clockwise: from left side
            - pp.Angle  # make the true north == 0
        )
        # into 8-direction
        direction_from_left = Direction(
            round(
                (
                    (bearing_from_left / (2 * math.pi))  # in rotations (from radian)
                    + 1  # add 1 rotation to make it always positive
                )
                * 8  # in 1/8 rotations
            )  # round to closest 1/8 rotations
            % 8  # remove full rotations, from adding 1 full rotation
            + 1  # make the true north == 1 instead of 0 (rotation)
        )  # convert it to Direction
        if i == 1:  # at the second point
            last_direction_from_left = direction_from_left
            continue
        if direction_from_left != last_direction_from_left:
            # create a line excluding this point
            wall_segments.append(
                (last_direction_from_left, LineString(wall_points[first_i:i]))
            )
            # last point will be shared between two lines
            first_i = i - 1
            # this bearing for next line
            last_direction_from_left = direction_from_left
    # for the last line
    wall_segments.append((last_direction_from_left, LineString(wall_points[first_i:])))

    # pprint(wall_segments)

    seg_buffers: Sequence[Tuple[Direction, Polygon, Polygon]] = []
    for dir, line in wall_segments:
        # 1 foot, flat cap, bevel join
        # a positive distance indicates the left-hand side
        left_buffer: Polygon = line.buffer(
            1, cap_style=2, join_style=3, single_sided=True
        )
        # a negative distance indicates the right-hand side
        right_buffer: Polygon = line.buffer(
            -1, cap_style=2, join_style=3, single_sided=True
        )

        seg_buffers.append((dir, left_buffer, right_buffer))

    for room in rooms:
        directions = set()
        for dir, left_buffer, right_buffer in seg_buffers:
            if (
                left_buffer.intersection(room_shapes[room]).area
                >= right_buffer.intersection(room_shapes[room]).area
            ):
                # if room is at left side
                directions.add(dir)
            else:
                # add opposite direction if right side
                directions.add(dir.opposite())

        room_opening_relations.append(
            RoomOpeningRelation(room, wall, tuple(directions))
        )

pprint(room_opening_relations)

# phase = pick_phase_by_views(doc)
# clr_phase = get_element(doc, phase)

# shell = rings[0]
# holes = rings[1:]


# room = Polygon(shell, holes)
# pprint(room.area)
# window = Point(loc.X, loc.Y)
# # pprint(nearest_points(room, window)[0].wkt)
# window_box = box(window.x - 1, window.y - 1, window.x + 1, window.y + 1)
# x = window_box.intersection(room)
# c = x.centroid
# pprint(c.wkt)
# pprint((window.x - c.x, window.y - c.y))


# # print(azimuth(Point(0, 0), Point(0, 1)))  # north == 0
# # print(azimuth(Point(0, 0), Point(1, 0)))  # east == 1/2*pi
# # print(azimuth(Point(0, 0), Point(0, -1)))  # south == pi
# # print(azimuth(Point(0, 0), Point(-1, 0)))  # west == 3/2*pi
# print(azimuth(c, window))  # azimuth from centroid to window: pi == south

# pl = doc.ActiveProjectLocation
# pp = pl.GetProjectPosition(DB.XYZ.Zero)
# print(pp.Angle)  # 0.64 from -pi to pi

# # the window is in true southeast. (small in azimuth)
# # angle difference between project north and true north should be subtracted.

# print(azimuth(c, window) - pp.Angle)
# print(
#     Direction(
#         round((((azimuth(c, window) - pp.Angle) / (2 * math.pi)) + 100) * 8) % 8 + 1
#     )
# )
