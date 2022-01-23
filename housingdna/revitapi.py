#! python3

from typing import (
    List,
    Tuple,
    Union,
    Optional,
)
import itertools
from pathlib import PurePath

from .model import RevitInfo

### if it's already used by pyrevit...
# import clr

# clr.AddReference("RevitAPI")
# clr.AddReference("RevitAPIUI")
# clr.AddReference("AdWindows")
# clr.AddReference("UIFramework")
# clr.AddReference("UIFrameworkServices")

try:
    from Autodesk.Revit import DB  # type: ignore
    from Autodesk.Revit.UI import UIApplication  # type: ignore
except:
    print("welcome, another lost soul...")

### revit interface


def get_revit_doc(uiapp: UIApplication):
    uidoc = uiapp.ActiveUIDocument
    doc = uidoc.Document
    return doc


def get_project_path(obj) -> Optional[str]:
    if hasattr(obj, "PathName"):
        return str(obj.PathName)
    elif hasattr(obj, "ActiveUIDocument"):
        return str(get_revit_doc(obj).PathName)
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
        elem = get_element(elem, doc)

    try:
        return str(elem.Name)
    except:
        pass
    try:
        return str(elem.get_Name())
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


def get_id(elem: Union[int, DB.ElementId, DB.Element]) -> int:
    if isinstance(elem, int):
        return elem
    elif isinstance(elem, DB.ElementId):
        try:
            return int(elem.get_IntegerValue())
        except:
            return int(elem.IntegerValue)

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


def get_element(id_: Union[int, DB.ElementId], doc: DB.Document):
    if isinstance(id_, int):
        id_ = DB.ElementId(id_)

    if isinstance(id_, DB.ElementId) and isinstance(doc, DB.Document):
        elem = doc.GetElement(id_)
        return elem
    else:
        raise Exception(f"no {id_} in {doc}")


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
        elem = get_element(elem, doc)

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
) -> float:
    if isinstance(room, (int, DB.ElementId)):
        if doc is None:
            raise
        room = get_element(room, doc)

    height = room.UnboundedHeight
    # height = room.GetParameter(DB.ParameterTypeId.RoomHeight).AsDouble()
    return float(height)


def is_on_phase(
    elem: Union[int, DB.ElementId, DB.Element],
    phase: Union[int, DB.ElementId, DB.Phase],
    doc: Optional[DB.Document] = None,
):
    if isinstance(elem, (int, DB.ElementId)):
        if doc is None:
            raise
        elem = get_element(elem, doc)

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


def get_true_north(doc: DB.Document) -> float:
    pl = doc.ActiveProjectLocation
    pp = pl.GetProjectPosition(DB.XYZ.Zero)
    return float(pp.Angle)  # in radian, from -pi to pi


def is_curtain_wall(
    wall: Union[int, DB.ElementId, DB.Wall], doc: Optional[DB.Document] = None
) -> bool:
    if isinstance(wall, (int, DB.ElementId)):
        if doc is None:
            raise
        wall = get_element(wall, doc)

    return bool(wall.WallType.Kind == DB.WallKind.Curtain)


def is_placed_room(
    room: Union[int, DB.ElementId, DB.Architecture.Room],
    doc: Optional[DB.Document] = None,
) -> bool:
    if isinstance(room, (int, DB.ElementId)):
        if doc is None:
            raise
        room = get_element(room, doc)

    # if not isinstance(room, DB.Architecture.Room):
    #     raise
    # assuming a room, won't check

    return bool(room.Area and room.Location)


def get_boundaries(
    room: Union[int, DB.ElementId, DB.Architecture.Room],
    phase: Optional[Union[int, DB.ElementId, DB.Phase]] = None,
    doc: Optional[DB.Document] = None,
) -> Optional[Tuple[int, ...]]:
    if isinstance(room, (int, DB.ElementId)):
        if doc is None:
            raise
        room = get_element(room, doc)

    if not isinstance(room, DB.Architecture.Room):
        raise
    # assuming a room

    # if the room in not on the phase
    if phase is not None and not is_on_phase(room, phase):
        return None

    try:
        boundary_opt = DB.SpatialElementBoundaryOptions()
        boundary_opt.SpatialElementBoundaryLocation = (
            DB.SpatialElementBoundaryLocation.Center
        )
        boundary_opt.StoreFreeBoundaryFaces = True

        seglistlist = room.GetBoundarySegments(boundary_opt)
        return tuple(
            int(seg.ElementId.IntegerValue)
            for seg in itertools.chain.from_iterable(seglistlist)
        )
    except:
        return tuple()


def get_from_to_rooms(
    elem: Union[int, DB.ElementId, DB.FamilyInstance],
    phase: Optional[Union[int, DB.ElementId, DB.Phase]] = None,
    doc: Optional[DB.Document] = None,
) -> Tuple[int, ...]:
    if isinstance(elem, (int, DB.ElementId)):
        if doc is None:
            raise
        elem = get_element(elem, doc)
    if isinstance(phase, (int, DB.ElementId)):
        if doc is None:
            raise
        phase = get_element(phase, doc)

    if not isinstance(elem, DB.FamilyInstance):
        raise
    # assuming a door or a window

    try:
        if phase is not None:
            # FromRoom Property (Phase)
            # https://www.revitapidocs.com/2022/c4a37990-0603-50e0-ca97-1cd5449940dd.htm
            from_room = elem.get_FromRoom(phase)
            to_room = elem.get_ToRoom(phase)
        else:
            # FromRoom Property: The "From Room" in the **last** phase of the project.
            from_room = elem.FromRoom
            to_room = elem.ToRoom
        return tuple(get_id(room) for room in set([from_room, to_room]) if room)
    except:
        return tuple()


def get_transparency(
    elem: Union[int, DB.ElementId, DB.FamilyInstance],
    doc: DB.Document,
) -> int:
    if isinstance(elem, (int, DB.ElementId)):
        # if doc is None:
        #     raise ValueError("doc")
        elem = get_element(elem, doc)

    if not isinstance(elem, DB.FamilyInstance):
        raise TypeError(type(elem))
    if not (
        elem.Category.Id.IntegerValue
        == DB.Category.GetCategory(doc, DB.BuiltInCategory.OST_Doors).Id.IntegerValue
    ):
        raise NotImplementedError(elem.Category.Name)

    material_ids = elem.Symbol.GetMaterialIds(False)  # not PaintMaterials

    results: List[Tuple[int, float, int]] = []

    for id_ in material_ids:
        material = get_element(id_, doc)
        results.append(
            (
                int(id_.IntegerValue),
                float(elem.GetMaterialArea(id_, False)),  # not PaintMaterials
                int(material.Transparency),
            )
        )

    max_area = max(result[1] for result in results)
    transparency = max(result[2] for result in results if result[1] >= max_area)
    return transparency


### housingDNA logic that interact with revit/clr objects


def pick_phase_by_views(doc: DB.Document) -> int:
    phases = [get_id(p) for p in doc.Phases]

    views = get_all_by_category(doc, DB.BuiltInCategory.OST_Views)
    view_phases = []
    for view in views:
        try:
            view_phases.append(
                get_parameter_value(view, DB.BuiltInParameter.VIEW_PHASE, doc)
            )
        except:
            pass

    # sanity check: there are phases in the views
    if not view_phases:
        raise

    # return the last phase in case of a tie
    return int(max(reversed(phases), key=view_phases.count))


def eval_curve(curve: DB.Curve, first=False, division=8) -> List[Tuple[float, float]]:
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
        points.append((float(point.X), float(point.Y)))

    return points


def get_points_2d(
    curve: DB.Curve, first=False, division=8
) -> List[Tuple[float, float]]:
    if isinstance(curve, DB.Line):
        if curve.IsBound:
            points = []

            for i in [0, 1] if first else [1]:
                point = curve.GetEndPoint(i)
                points.append((float(point.X), float(point.Y)))

            return points
        else:
            raise  # no unbound line
    else:
        return eval_curve(curve, first, division)


def get_location_2d(
    elem: Union[int, DB.ElementId, DB.FamilyInstance],
    doc: Optional[DB.Document] = None,
) -> Optional[Tuple[float, float]]:
    if isinstance(elem, (int, DB.ElementId)):
        if doc is None:
            raise
        elem = get_element(elem, doc)

    if not isinstance(elem, DB.FamilyInstance):
        raise
    # assuming a door or a window

    try:
        loc = elem.Location.Point
        return (float(loc.X), float(loc.Y))
    except:
        return None


def get_shape_2d(
    elem: Union[int, DB.ElementId, DB.Wall, DB.ModelCurve],
    division=8,
    doc: Optional[DB.Document] = None,
) -> Optional[List[Tuple[float, float]]]:
    if isinstance(elem, (int, DB.ElementId)):
        if doc is None:
            raise
        elem = get_element(elem, doc)

    if not isinstance(elem, (DB.Wall, DB.ModelCurve)):
        raise
    # assuming a wall or a separation line

    try:
        return get_points_2d(elem.Location.Curve, first=True)
    except:
        return None


def get_boundary_2d(
    elem: Union[int, DB.ElementId, DB.SpatialElement],
    division=8,
    doc: Optional[DB.Document] = None,
) -> Optional[List[List[Tuple[float, float]]]]:
    if isinstance(elem, (int, DB.ElementId)):
        if doc is None:
            raise
        elem = get_element(elem, doc)

    if not isinstance(elem, DB.SpatialElement):
        raise
    # assuming a room

    try:
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
    except:
        return None


def get_revit_info(uiapp: UIApplication) -> RevitInfo:
    doc = get_revit_doc(uiapp)

    print("preparing...")
    r = RevitInfo()  # return data class

    r.doc_name = (
        PurePath(doc_path).name if (doc_path := get_project_path(uiapp)) else None
    )
    r.true_north = get_true_north(doc)

    r.phase = pick_phase_by_views(doc)

    print("get elements...")
    all_rooms = get_all_by_category(doc, DB.BuiltInCategory.OST_Rooms)
    r.rooms = [room for room in all_rooms if is_placed_room(room, doc)]

    r.doors = get_all_by_category(doc, DB.BuiltInCategory.OST_Doors)
    r.windows = get_all_by_category(doc, DB.BuiltInCategory.OST_Windows)

    walls = get_all_by_category(doc, DB.BuiltInCategory.OST_Walls)
    r.curtain_walls = [wall for wall in walls if is_curtain_wall(wall, doc)]
    r.separation_lines = get_all_by_category(
        doc, DB.BuiltInCategory.OST_RoomSeparationLines
    )

    print("get attributes...")
    r.names = {elem: get_name(elem, doc) for elem in r.rooms}
    r.heights = {elem: get_unbounded_height(elem, doc) for elem in r.rooms}
    r.transparencies = {elem: get_transparency(elem, doc) for elem in r.doors}
    print("wait...")
    r.boundary_segments = {
        elem: set(segs)
        for elem in r.rooms
        if (segs := get_boundaries(elem, r.phase, doc))
    }

    r.rel_rooms = {}
    # from room and to room of doors and windows
    for elem in r.doors + r.windows:
        r.rel_rooms.setdefault(elem, set()).update(
            get_from_to_rooms(elem, r.phase, doc)
        )
    # rooms bounded curtain walls and separation lines
    for room, segs in r.boundary_segments.items():
        for elem in segs:
            if elem in r.curtain_walls + r.separation_lines:
                r.rel_rooms.setdefault(elem, set()).add(room)

    print("get shapes...")
    # 2d point for doors and windows
    r.points = {
        elem: loc for elem in r.doors + r.windows if (loc := get_location_2d(elem, doc))
    }
    # 2d polyline for walls and lines
    r.lines = {
        elem: shape
        for elem in r.curtain_walls + r.separation_lines
        if (shape := get_shape_2d(elem, doc=doc))
    }
    # 2d rings (with shell in [0] and holes in [1:]) for rooms
    r.boundaries = {
        elem: rings for elem in r.rooms if (rings := get_boundary_2d(elem, doc=doc))
    }

    print("done with revit 👋")
    return r
