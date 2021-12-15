from typing import Sequence, Set, Tuple
import itertools

from .model import House, Length, RevitObject, Room, RoomConnection

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


def get_project_path(obj):
    if hasattr(obj, "PathName"):
        return obj.PathName
    elif hasattr(obj, "ActiveUIDocument"):
        return get_revit_doc(obj).PathName
    else:
        return None


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


def get_room_connections(clr_rooms, clr_doors, id_sep_lines) -> Set[RoomConnection]:
    opt = DB.SpatialElementBoundaryOptions()
    opt.SpatialElementBoundaryLocation = DB.SpatialElementBoundaryLocation.Center

    room_connections = set()

    # get room connections by doors
    for door in clr_doors:
        if door.FromRoom and door.ToRoom:
            if door.FromRoom != door.ToRoom:
                room_connections.add(
                    RoomConnection(
                        *sorted(map(get_id, (door.FromRoom, door.ToRoom))),
                        type_=RevitObject.DOOR,
                    )
                )

    # get room connections by room separation lines
    sep_rooms_dict = dict()
    for room in clr_rooms:
        id_room = get_id(room)

        boundaries = itertools.chain.from_iterable(room.GetBoundarySegments(opt))
        id_boundaries = list(map(get_id, boundaries))
        for id_ in id_boundaries:
            if id_ in id_sep_lines:
                sep_rooms_dict.setdefault(id_, set()).add(id_room)

    id_rooms_separated: Set[int]
    for id_rooms_separated in sep_rooms_dict.values():
        if len(id_rooms_separated) >= 2:
            for id_pair in itertools.combinations(id_rooms_separated, 2):
                room_connections.add(
                    RoomConnection(
                        *sorted(id_pair),
                        type_=RevitObject.ROOM_SEPARATION_LINE,
                    )
                )

    return room_connections


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
        if room.Area and room.Location
    }

    _id_sep_lines = sorted(map(get_id, clr_sep_lines))
    room_conns = get_room_connections(clr_rooms, clr_doors, _id_sep_lines)

    return House(
        rooms=tuple(rooms_dict.values()),
        room_connections=tuple(room_conns),
    )
