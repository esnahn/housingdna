from enum import Enum, auto, unique
import json
from pathlib import Path, PurePath
from itertools import combinations
import dataclasses
from dataclasses import dataclass, field
from typing import (
    Any,
    Dict,
    Iterable,
    Iterator,
    List,
    Literal,
    Optional,
    Protocol,
    Set,
    Tuple,
    Union,
)

# raw (as you can get) data model from Revit
@dataclass
class RevitInfo:
    doc_name: Optional[str] = None
    true_north: float = 0

    phase: Optional[int] = None
    rooms: List[int] = field(default_factory=list)
    doors: List[int] = field(default_factory=list)
    windows: List[int] = field(default_factory=list)
    curtain_walls: List[int] = field(default_factory=list)
    separation_lines: List[int] = field(default_factory=list)

    names: Dict[int, str] = field(default_factory=dict)
    heights: Dict[int, float] = field(default_factory=dict)
    transparencies: Dict[int, int] = field(default_factory=dict)
    boundary_segments: Dict[int, Set[int]] = field(default_factory=dict)
    rel_rooms: Dict[int, Set[int]] = field(default_factory=dict)
    points: Dict[int, Tuple[float, float]] = field(default_factory=dict)
    lines: Dict[int, List[Tuple[float, float]]] = field(default_factory=dict)
    boundaries: Dict[int, List[List[Tuple[float, float]]]] = field(default_factory=dict)


### Dataclasses for the housing model


@unique
class RevitObject(Enum):
    """Object type enum of/based on Revit categories."""

    DOOR = auto()
    ROOM_SEPARATION_LINE = auto()
    WINDOW = auto()
    CURTAIN_WALL = auto()
    # BASIC_WALL


Access = Literal[RevitObject.DOOR, RevitObject.ROOM_SEPARATION_LINE]


class Direction(Enum):
    """Compass directions Enum in horizontal 8 ways and vertical 2 ways.

    >>> dir_list = [Direction.SOUTH, Direction.SOUTHEAST]
    >>> Direction.SOUTH in dir_list
    True
    >>> Direction.NORTH in dir_list
    False

    >>> Direction.NORTH < Direction.NORTHEAST  # not int
    Traceback (most recent call last):
        ...
    TypeError: '<' not supported between instances of 'Direction' and 'Direction'
    """

    NORTH = 1
    NORTHEAST = 2
    EAST = 3
    SOUTHEAST = 4
    SOUTH = 5
    SOUTHWEST = 6
    WEST = 7
    NORTHWEST = 8

    UP = 1024
    DOWN = -1024

    def opposite(self):
        """Return the opposite direction of itself.

        >>> d = Direction.NORTH
        >>> d.opposite()
        <Direction.SOUTH: 5>
        >>> Direction.SOUTH.opposite()
        <Direction.NORTH: 1>
        >>> Direction.SOUTHEAST.opposite()
        <Direction.NORTHWEST: 8>

        >>> Direction.UP.opposite()
        <Direction.DOWN: -1024>
        """

        if 1 <= self.value <= 8:
            return Direction((self.value - 1 + 4) % 8 + 1)
        elif self is Direction.UP or self is Direction.DOWN:
            return Direction(-self.value)
        else:
            raise Exception(f"{self} can't be happening")


def multiple_sides(directions: Set[Direction]) -> bool:
    """Check if there are directions that point different sides.

    fuzziness makes two neighboring directions equal to each other.
    >>> dir_set = {Direction.NORTH, Direction.NORTHEAST}
    >>> multiple_sides(dir_set)
    False

    Difference beyond fuzziness returns True.
    >>> dir_set = {Direction.NORTH, Direction.EAST}
    >>> multiple_sides(dir_set)
    True

    Up and down are their own differentiated side.
    >>> dir_set = {Direction.NORTH, Direction.UP}
    >>> multiple_sides(dir_set)
    True
    >>> dir_set = {Direction.UP, Direction.DOWN}
    >>> multiple_sides(dir_set)
    True
    """

    num_directions = 8
    fuzziness = 1

    vertical = 1000
    return any(
        # they are different in 3-dimensional way
        (abs(a.value - b.value) > vertical)
        or (  # or,
            # they are different enough in 2d plane
            abs(a.value - b.value) > fuzziness
            # and it is not because they are wrapping around
            and (abs(a.value - b.value) < num_directions - fuzziness)
        )
        for a, b in combinations(directions, 2)
    )  # in any combination of two directions


@dataclass(frozen=True)
class Length:
    """Length in milimeters.

    >>> Length(1000)
    Length(mm=1000)

    Rounds up the value to 2 decimal places.
    >>> Length(100.12345)
    Length(mm=100.12)

    Can convert from feet, which is the internal unit of length in Revit.
    One foot is defined as 0.3048 meters exactly, So the value in the next
    example was not rounded up.
    >>> Length.from_ft(6)
    Length(mm=1828.8)
    """

    mm: float

    def __post_init__(self):
        # limits the precision
        object.__setattr__(self, "mm", round(self.mm, 2))

    @classmethod
    def from_ft(cls, val_in_feet: Union[float, int]):
        return cls(val_in_feet * 304.8)


@dataclass(frozen=True)
class Room:
    """Room.

    Details are subject to change.

    >>> living_room = Room(element_id=0, name='거실', height=Length.from_ft(10))
    >>> kitchen = Room(element_id=1, name='주방', height=Length.from_ft(10))

    Room can be a key in dicts.
    >>> {living_room: living_room.name}
    {Room(element_id=0, name='거실', height=Length(mm=3048.0)): '거실'}

    A tuple of two Rooms will represent a connection between them.
    >>> connection = (living_room, kitchen)

    ElementIds of Rooms in the same Revit model are unique.
    But, This dataclass does not check nor prevent id collision.
    Therefore, you can create "same" rooms with different attributes.
    >>> bedroom = Room(element_id=0, name='침실', height=Length.from_ft(8))

    They are equal, as in having same elementId.
    >>> living_room == bedroom
    True

    They will be treated as same and deduplicated in sets.
    >>> room_set = {living_room}
    >>> room_set.add(bedroom)
    >>> print(room_set)
    {Room(element_id=0, name='거실', height=Length(mm=3048.0))}

    Even though they are not the same object.
    >>> living_room is bedroom
    False
    >>> id(living_room) == id(bedroom)
    False
    """

    element_id: int
    name: str = field(compare=False)
    height: Length = field(compare=False)


@dataclass(frozen=True)
class Glazing:
    """A transparent boundary of room(s).

    A glazed window, a glass door, a curtain wall, or an imaginary line that
    separates rooms.

    Openings with same elementId will be treated as same and deduplicated in sets.
    """

    element_id: int
    type_: RevitObject = field(compare=False)
    outmost: bool = field(compare=False)


@dataclass(frozen=True)
class RoomConnection:
    """A connection between room A and room B."""

    a_id: int
    b_id: int
    type_: Access  # A subset of revit objects that allows access through it.


@dataclass(frozen=True)
class RoomGlazingRelation:
    """A relation between a room and a glazing.

    The facing indicates the compass direction from a room to a glazing.
    A room can face a glazing in multiple directions."""

    room_id: int
    glazing_id: int
    facings: Tuple[Direction, ...] = field(compare=False)


@dataclass(frozen=True)
class House:
    """Model of a house for the housing DNA analysis.

    >>> living_room = Room(element_id=0, name='거실', height=Length.from_ft(10))
    >>> kitchen = Room(element_id=1, name='주방', height=Length.from_ft(10))
    >>> bedroom = Room(element_id=2, name='침실', height=Length.from_ft(8))

    >>> bed_window = Glazing(10, RevitObject.WINDOW, outmost=True)
    >>> ldk_line = Glazing(11, RevitObject.ROOM_SEPARATION_LINE, outmost=False)

    >>> rooms = (living_room, kitchen, bedroom)
    >>> glazings = (bed_window, ldk_line)

    >>> conns = (
    ...     RoomConnection(
    ...         a_id=living_room.element_id,
    ...         b_id=kitchen.element_id,
    ...         type_=RevitObject.ROOM_SEPARATION_LINE,
    ...     ),
    ...     RoomConnection(
    ...         a_id=living_room.element_id,
    ...         b_id=bedroom.element_id,
    ...         type_=RevitObject.DOOR,
    ...     ),
    ... )

    >>> rels = (
    ...     RoomGlazingRelation(
    ...         bedroom.element_id,
    ...         bed_window.element_id,
    ...         (Direction.SOUTH,),
    ...     ),
    ...     RoomGlazingRelation(
    ...         living_room.element_id,
    ...         ldk_line.element_id,
    ...         (Direction.EAST,),
    ...     ),
    ...     RoomGlazingRelation(
    ...         kitchen.element_id,
    ...         ldk_line.element_id,
    ...         (Direction.WEST,),  # opposite of facing from living room
    ...     ),
    ... )

    >>> house = House(
    ...     rooms=rooms,
    ...     room_connections=conns,
    ...     glazings=glazings,
    ...     room_glazing_relations=rels,
    ... )
    >>> house  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    House(rooms=(Room(element_id=0, name='거실', height=Length(mm=3048.0)), ...
    RoomGlazingRelation(room_id=1, glazing_id=11, facings=(<Direction.WEST: 7>,))))
    >>> house.to_json("test.json")
    >>> d = House.from_json("test.json")
    >>> house == d
    True
    """

    rooms: Tuple[Room, ...] = tuple()
    room_connections: Tuple[RoomConnection, ...] = tuple()
    glazings: Tuple[Glazing, ...] = tuple()
    room_glazing_relations: Tuple[RoomGlazingRelation, ...] = tuple()

    def to_json(self, path: Union[str, Path, PurePath]):
        filepath = Path(path)
        if not filepath.parent.exists():
            filepath.parent.mkdir(parents=True)

        with open(str(filepath), "w", encoding="utf-8") as file:
            json.dump(
                self, file, ensure_ascii=False, indent=4, cls=DataclassJSONEncoder
            )

    @classmethod
    def from_json(cls, path: Union[str, Path, PurePath]):
        with open(str(path), encoding="utf-8") as file:
            obj = json.load(file, object_hook=to_nested_dataclass)
        return obj if isinstance(obj, cls) else None


# type of a dataclass
# https://stackoverflow.com/questions/54668000/type-hint-for-an-instance-of-a-non-specific-dataclass
class IsDataclass(Protocol):
    # dataclasses._FIELDS
    __dataclass_fields__: Dict[str, Any]


E = Union[str, int, float, Enum]

# nested dict
ND = Union[List[Any], Tuple[Any, ...], Dict[E, Any], E]

# nested dataclass
DC = Union[IsDataclass, ND]


def is_dataclass_instance(obj: DC) -> bool:
    """Returns True if a class is an instance of a dataclass (and not a
    dataclass itself)

    same as dataclasses._is_dataclass_instance()
    """
    return hasattr(type(obj), "__dataclass_fields__")


def as_nested_dict(obj: DC):
    """Converts dataclasses to dicts in a nested data object.

    Accept an object consisting of dataclasses, lists, tuples, and dicts, and
    their elements.

    Dataclassess will be converted to dicts. The key "__dataclass__" that has
    a value of `obj.__class__.__name__` will be added whenever a dataclass is
    converted.

    Lists, tuples, and dicts will be iterated and searched for dataclasses inside.
    Other types of objects will be returned as is.

    Enums will be converted to dicts, with the key "__enum__" that has a value
    of `str(obj)`.
    """
    if is_dataclass_instance(obj):
        result_list: List[Tuple[str, DC]] = []
        for f in dataclasses.fields(obj):
            # recursive
            value: DC = as_nested_dict(getattr(obj, f.name))  # type: ignore
            result_list.append((f.name, value))

        result_list.append(("__dataclass__", obj.__class__.__name__))
        return dict(result_list)

    elif isinstance(obj, Iterable):
        if isinstance(obj, dict):
            result_dict: Dict[E, ND] = {key: as_nested_dict(obj[key]) for key in obj}
            return result_dict

        iter: Iterator[ND] = (as_nested_dict(e) for e in obj)
        if isinstance(obj, list):
            return list(iter)
        elif isinstance(obj, tuple):
            return tuple(iter)

    elif isinstance(obj, Enum):
        # https://stackoverflow.com/a/24482806
        return {"__enum__": str(obj)}
    return obj


class DataclassJSONEncoder(json.JSONEncoder):
    def default(self, o: IsDataclass):
        if is_dataclass_instance(o):
            return as_nested_dict(o)
        else:
            raise TypeError(type(o))
        return super().default(o)


def to_nested_dataclass(obj: ND):
    """Converts special dicts back to dataclasses in a nested data object.

    Accept an object consisting of dicts, lists, tuples, and
    their elements.

    Dicts that are converted from dataclassess have a key named "__dataclass__"
    which holds the class name. Those dicts will be converted back to dataclass
    of matching name.

    Dicts that are converted from enums have a key named "__enum__" which holds
    a string representation of an enum. Those dicts will be converted back to
    enum member of matching class and names.

    Lists and tuples (which were saved as JSON arrays) are converted to tuples.
    """

    if isinstance(obj, dict):
        class_: str = obj.pop("__dataclass__", None)  # type: ignore
        if class_:
            result_list: List[Tuple[E, DC]] = []
            for key in obj:
                # recursive
                value: DC = to_nested_dataclass(obj[key])  # type: ignore
                result_list.append((key, value))
            return globals()[class_](**dict(result_list))
        elif "__enum__" in obj:
            # https://stackoverflow.com/a/24482806
            repr: str = obj["__enum__"]  # type: ignore
            name, member = repr.split(".")
            if issubclass(class_ := globals()[name], Enum):
                return getattr(class_, member)
        else:
            return_dict: Dict[E, DC] = {
                key: to_nested_dataclass(obj[key]) for key in obj
            }
            return return_dict
    elif isinstance(obj, Iterable):
        iter: Iterator[DC] = (to_nested_dataclass(e) for e in obj)

        if isinstance(obj, list) or isinstance(obj, tuple):
            return tuple(iter)

    return obj


if __name__ == "__main__":
    import doctest

    doctest.testmod()
