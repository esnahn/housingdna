#! python3
# type: ignore

from typing import Mapping, NamedTuple, Sequence, Set, Tuple, Union, Optional
import itertools

from .model import House, Length, RevitObject, Room, RoomConnection

import clr

clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")
clr.AddReference("AdWindows")
clr.AddReference("UIFramework")
clr.AddReference("UIFrameworkServices")

from Autodesk.Revit import DB  # type: ignore
from Autodesk.Revit.UI import UIApplication

### revit interface


def get_revit_doc(uiapp: UIApplication):
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


def get_all_by_category(doc: DB.Document, category):
    collector = (
        DB.FilteredElementCollector(doc)
        .OfCategory(category)
        .WhereElementIsNotElementType()
    )
    return [get_id(elem) for elem in collector]


def get_all_by_class(doc: DB.Document, type_):
    collector = (
        DB.FilteredElementCollector(doc).OfClass(type_).WhereElementIsNotElementType()
    )
    return [get_id(elem) for elem in collector]


def get_name(
    elem: Union[int, DB.ElementId, DB.Element], doc: Optional[DB.Document] = None
):
    if isinstance(elem, (int, DB.ElementId)):
        if doc is None:
            raise
        elem = get_element(doc, elem)

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


def get_id(
    elem: Union[int, DB.ElementId, DB.Element], doc: Optional[DB.Document] = None
):
    if isinstance(elem, int):
        return elem
    elif isinstance(elem, DB.ElementId):
        return elem.IntegerValue

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


def get_element(doc: DB.Document, id_: Union[int, DB.ElementId]):
    if isinstance(id_, int):
        id_ = DB.ElementId(id_)

    elem = None
    if isinstance(id_, DB.ElementId):
        elem = doc.GetElement(id_)
    return elem


def get_parameter_value(
    elem: Union[int, DB.ElementId, DB.Element],
    # pythonnet converts .NET enums to int, for now, and it is "fixed" in 3.0.0.
    # https://stackoverflow.com/questions/65805093/pythonnet-why-are-net-enums-type-casted-to-int
    # check both in case enum conversion is "fixed"
    built_in_parameter: Union[(int, DB.BuiltInParameter)],
    doc: Optional[DB.Document] = None,
):
    if isinstance(elem, (int, DB.ElementId)):
        if doc is None:
            raise
        elem = get_element(doc, elem)

    param: DB.Parameter = elem.get_Parameter(built_in_parameter)
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
    else:  # ???
        raise


def get_unbounded_height(
    room: Union[int, DB.ElementId, DB.Architecture.Room],
    doc: Optional[DB.Document] = None,
) -> Length:
    if isinstance(elem, (int, DB.ElementId)):
        if doc is None:
            raise
        elem = get_element(doc, elem)

    height = room.UnboundedHeight
    # height = room.GetParameter(DB.ParameterTypeId.RoomHeight).AsDouble()
    return Length.from_ft(height)


def is_on_phase(
    elem: Union[int, DB.ElementId, DB.Element],
    phase: Union[int, DB.ElementId, DB.Phase],
    doc: Optional[DB.Document] = None,
):
    if isinstance(elem, (int, DB.ElementId)):
        if doc is None:
            raise
        elem = get_element(doc, elem)

    if isinstance(phase, int):
        phase = DB.ElementId(phase)
    elif isinstance(phase, DB.Phase):
        phase = phase.Id

    on_phase_enums = [
        DB.ElementOnPhaseStatus.Existing,  # 2
        DB.ElementOnPhaseStatus.New,  # 4
        # or, at least, it does not have phase set
        # None name is reserved, throws error
        getattr(DB.ElementOnPhaseStatus, "None"),  # 0
    ]

    return elem.GetPhaseStatus(phase) in on_phase_enums


### housingDNA logic that interact with revit/clr objects


def pick_phase_by_views(doc: DB.Document) -> int:
    phases = [get_id(p) for p in doc.Phases]

    views = get_all_by_category(doc, DB.BuiltInCategory.OST_Views)
    view_phases = []
    for view in views:
        try:
            view_phases.append(
                get_parameter_value(view, DB.BuiltInParameter.VIEW_PHASE)
            )
        except:
            pass
    # return the last phase in case of a tie
    return int(max(reversed(phases), key=view_phases.count))


# TODO: Separate clr calls and pure python logic


def get_room_connections(
    clr_rooms: Sequence,
    clr_doors: Sequence,
    id_sep_lines: Sequence,
    phase=None,
) -> Set[RoomConnection]:
    if phase is not None:
        assert isinstance(phase, DB.Phase)
        phase_id = phase.Id
    else:
        phase_id = None

    opt = DB.SpatialElementBoundaryOptions()
    opt.SpatialElementBoundaryLocation = DB.SpatialElementBoundaryLocation.Center

    room_connections = set()

    # get room connections by doors
    for door in clr_doors:
        if phase is not None:
            # FromRoom Property (Phase)
            # https://www.revitapidocs.com/2022/c4a37990-0603-50e0-ca97-1cd5449940dd.htm
            from_room = door.get_FromRoom(phase)
            to_room = door.get_ToRoom(phase)
        else:
            # FromRoom Property: The "From Room" in the **last** phase of the project.
            from_room = door.FromRoom
            to_room = door.ToRoom

        if from_room and to_room:
            if from_room != to_room:
                room_connections.add(
                    RoomConnection(
                        # sort the ids of two rooms
                        *sorted(map(get_id, (from_room, to_room))),
                        type_=RevitObject.DOOR,
                    )
                )

    # get room connections by room separation lines
    sep_rooms_dict = dict()
    for room in clr_rooms:
        if phase is not None and not is_on_phase(room, phase_id):
            continue

        boundaries = itertools.chain.from_iterable(room.GetBoundarySegments(opt))
        id_boundaries = list(map(get_id, boundaries))
        for id_ in id_boundaries:
            if id_ in id_sep_lines:
                sep_rooms_dict.setdefault(id_, set()).add(get_id(room))

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
    phase_id = pick_phase_by_views(doc)
    phase = get_element(doc, phase_id)

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
    room_conns = get_room_connections(clr_rooms, clr_doors, _id_sep_lines, phase)

    return House(
        rooms=tuple(rooms_dict.values()),
        room_connections=tuple(room_conns),
    )
