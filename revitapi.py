from typing import Sequence, Set, Tuple
import itertools

from .model import *

import clr

clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")
clr.AddReference("AdWindows")
clr.AddReference("UIFramework")
clr.AddReference("UIFrameworkServices")

from Autodesk.Revit import DB  # type: ignore

# error
# from dynamo
# from RevitServices.Persistence import DocumentManager
# doc = DocumentManager.Instance.CurrentDBDocument

# error
# https://github.com/eirannejad/pyRevit/blob/master/pyrevitlib/pyrevit/__init__.py
# from pyrevit import _HostApplication
#
# hostapp = _HostApplication()
# doc = hostapp.doc
# print(doc)


def get_revit_doc(uiapp):
    uidoc = uiapp.ActiveUIDocument
    doc = uidoc.Document
    return doc


def get_all_by_category(doc, category):
    collector = (
        DB.FilteredElementCollector(doc)
        .OfCategory(category)
        .WhereElementIsNotElementType()
    )
    return [elem for elem in collector]


def get_unbounded_height(room):
    height = room.UnboundedHeight
    # height = room.GetParameter(DB.ParameterTypeId.RoomHeight).AsDouble()
    return Length.from_ft(height)


def get_name(elem):
    # .NET property not accessible in derived classes
    # where only the setter or the getter has been overridden
    # https://github.com/pythonnet/pythonnet/issues/1455

    # element_type = clr.GetClrType(DB.Element)
    # print(elem.GetType().BaseType.BaseType.FullName)

    # SpatialElement overrides only the setter, so we use Element's getter.
    return str(clr.GetClrType(DB.Element).GetProperty("Name").GetValue(elem))


def get_id(elem):
    if isinstance(elem, DB.Element):
        id_ = clr.GetClrType(DB.Element).GetProperty("Id").GetValue(elem).IntegerValue
    elif type(elem) == DB.BoundarySegment:
        id_ = elem.ElementId.IntegerValue
    else:
        print(type(elem))
        id_ = -1  # return error
    return int(id_)


def get_room_connections(clr_rooms, clr_doors, id_sep_lines) -> Set[Tuple[int, int]]:
    opt = DB.SpatialElementBoundaryOptions()
    opt.SpatialElementBoundaryLocation = DB.SpatialElementBoundaryLocation.Center

    id_room_connections = set()

    # get room connections by doors
    for door in clr_doors:
        if door.FromRoom and door.ToRoom:
            if door.FromRoom != door.ToRoom:
                id_room_connections.add(
                    tuple(sorted(map(get_id, (door.FromRoom, door.ToRoom))))
                )

    # get room connections by room separation lines
    sep_rooms_dict = dict()
    for room in clr_rooms:
        id_room = get_id(room)

        boundaries = itertools.chain.from_iterable(room.GetBoundarySegments(opt))
        id_boundaries = map(get_id, boundaries)
        for id_ in id_boundaries:
            if id_ in id_sep_lines:
                sep_rooms_dict.setdefault(id_, set()).add(id_room)

    for rooms in sep_rooms_dict.values():
        if len(rooms) >= 2:
            for pair in itertools.combinations(rooms, 2):
                id_room_connections.add(tuple(sorted(pair)))

    return id_room_connections


def get_model(uiapp):
    doc = get_revit_doc(uiapp)

    clr_rooms = get_all_by_category(doc, DB.BuiltInCategory.OST_Rooms)
    clr_walls = get_all_by_category(doc, DB.BuiltInCategory.OST_Walls)
    clr_doors = get_all_by_category(doc, DB.BuiltInCategory.OST_Doors)
    clr_sep_lines = get_all_by_category(doc, DB.BuiltInCategory.OST_RoomSeparationLines)

    rooms_dict = {
        (id_ := get_id(room)): Room(
            element_id=id_,
            name=get_name(room),
            height=get_unbounded_height(room),
        )
        for room in clr_rooms
    }

    _id_sep_lines = sorted(map(get_id, clr_sep_lines))
    _id_room_connections = get_room_connections(clr_rooms, clr_doors, _id_sep_lines)
    room_conns = tuple((rooms_dict[a], rooms_dict[b]) for a, b in _id_room_connections)

    return House(
        rooms=tuple(rooms_dict.values()),
        room_connections=room_conns,
    )
