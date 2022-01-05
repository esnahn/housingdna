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


### revit interface


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


def get_all_by_class(doc, type_):
    collector = (
        DB.FilteredElementCollector(doc).OfClass(type_).WhereElementIsNotElementType()
    )
    return [elem for elem in collector]


def get_name(elem):
    try:
        return str(elem.Name)
    except:
        pass

    # .NET property not accessible in derived classes
    # where only the setter or the getter has been overridden
    # https://github.com/pythonnet/pythonnet/issues/1455

    # element_type = clr.GetClrType(DB.Element)
    # print(elem.GetType().BaseType.BaseType.FullName)

    # SpatialElement overrides only the setter, so we use Element's getter.
    try:
        return str(clr.GetClrType(DB.Element).GetProperty("Name").GetValue(elem))
    except:
        pass

    raise Exception(f"get_name could not handle {type(elem)}")


def get_id(elem):
    try:
        return int(elem.Id.IntegerValue)
    except:
        pass

    if isinstance(elem, DB.Element):
        id_ = clr.GetClrType(DB.Element).GetProperty("Id").GetValue(elem).IntegerValue
    elif type(elem) == DB.BoundarySegment:
        id_ = elem.ElementId.IntegerValue
    else:
        raise Exception(f"get_id could not handle {type(elem)}")
    return int(id_)


def get_element(doc, id_):
    assert isinstance(doc, DB.Document)
    assert isinstance(id_, (int, DB.ElementId))

    if isinstance(id_, int):
        id_ = DB.ElementId(id_)

    elem = None
    if isinstance(id_, DB.ElementId):
        elem = doc.GetElement(id_)
    return elem


def get_parameter_value(elem, built_in_parameter):
    assert isinstance(elem, DB.Element)
    # pythonnet converts .NET enums to int, for now, and it is "fixed" in 3.0.0.
    # https://stackoverflow.com/questions/65805093/pythonnet-why-are-net-enums-type-casted-to-int

    # check both in case enum conversion is "fixed"
    assert isinstance(built_in_parameter, (int, DB.BuiltInParameter))

    param = elem.get_Parameter(built_in_parameter)

    if isinstance(param, DB.Parameter):
        storage_type = int(param.StorageType)
        # None  	None represents an invalid storage type. This value should not be used.
        # Integer	The internal data is stored in the form of a signed 32 bit integer.
        # Double	The data will be stored internally in the form of an 8 byte floating point number.
        # String	The internal data will be stored in the form of a string of characters.
        # ElementId	The data type represents an element and is stored as the id of the element.

        if storage_type == 1:  # Integer
            return int(param.AsInteger())
        elif storage_type == 2:  # Double
            return float(param.AsDouble())
        elif storage_type == 3:  # String
            return str(param.AsString())
        elif storage_type == 4:  # ElementId
            return int(param.AsElementId().IntegerValue)
        elif storage_type == 0:  # None, an invalid storage type
            return None

    return None  # ???


def get_unbounded_height(room):
    height = room.UnboundedHeight
    # height = room.GetParameter(DB.ParameterTypeId.RoomHeight).AsDouble()
    return Length.from_ft(height)


### housingDNA logic that interact with revit/clr objects


def pick_phase_by_views(doc):
    assert isinstance(doc, DB.Document)

    phase_ids = [get_id(p) for p in doc.Phases]

    clr_views = get_all_by_category(doc, DB.BuiltInCategory.OST_Views)
    view_phase_ids = [
        get_parameter_value(v, DB.BuiltInParameter.VIEW_PHASE)
        for v in clr_views
        if isinstance(v, DB.View)
    ]

    # return the last phase in case of a tie
    return max(reversed(phase_ids), key=view_phase_ids.count)


def get_room_connections(clr_rooms, clr_doors, id_sep_lines) -> Set[RoomConnection]:
    opt = DB.SpatialElementBoundaryOptions()
    opt.SpatialElementBoundaryLocation = DB.SpatialElementBoundaryLocation.Center

    room_connections = set()

    # get room connections by doors
    for door in clr_doors:
        # TODO: fromroom toroom 의존하지 않기; 비어있는 경우가 있음
        # Revit From/To Room field blank
        # https://knowledge.autodesk.com/support/revit/troubleshooting/caas/sfdcarticles/sfdcarticles/Revit-From-To-Room-field-blank-in-Door-schedule.html
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
