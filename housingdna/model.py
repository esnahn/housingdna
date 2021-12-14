from enum import Enum
import json
from pathlib import Path, PurePath
from itertools import combinations
import dataclasses
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Mapping, Sequence, Set, Tuple


class Direction(Enum):
    """Compass directions Enum in 8 ways.

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


def multiple_sides(directions: Set) -> bool:
    """Check if there are directions that point different sides.

    fuzziness makes two neighboring directions equal to each other.
    >>> dir_set = {Direction.NORTH, Direction.NORTHEAST}
    >>> multiple_sides(dir_set)
    False

    Difference beyond fuzziness returns True.
    >>> dir_set.add(Direction.EAST)
    >>> print("Multiple sides" if multiple_sides(dir_set) else "Nope")
    Multiple sides
    """

    num_directions = 8
    fuzziness = 1
    return any(
        abs(a.value - b.value) > fuzziness
        and abs(a.value - b.value) < num_directions - fuzziness
        for a, b in combinations(directions, 2)
    )


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
    def from_ft(cls, val_in_feet):
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
class House:
    """Model of a house for the housing DNA analysis.

    >>> living_room = Room(element_id=0, name='거실', height=Length.from_ft(10))
    >>> kitchen = Room(element_id=1, name='주방', height=Length.from_ft(10))
    >>> bedroom = Room(element_id=2, name='침실', height=Length.from_ft(8))

    >>> rooms = (living_room, kitchen, bedroom)
    >>> conns = (
    ...     (living_room.element_id, kitchen.element_id),
    ...     (living_room.element_id, bedroom.element_id),
    ... )

    >>> house = House(rooms=rooms, room_connections=conns)
    >>> house  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    House(rooms=(Room(element_id=0, name='거실', height=Length(mm=3048.0)), ...
            room_connections=((0, 1), (0, 2)))

    >>> house.to_json("test.json")
    >>> d = House.from_json("test.json")
    >>> house == d
    True
    """

    rooms: Tuple[Room, ...]
    room_connections: Tuple[Tuple[int, int], ...]

    def to_json(self, path):
        filepath = Path(path)
        if not filepath.parent.exists():
            filepath.parent.mkdir(parents=True)

        with open(str(filepath), "w", encoding="utf-8") as file:
            json.dump(
                self, file, ensure_ascii=False, indent=4, cls=DataclassJSONEncoder
            )

    @classmethod
    def from_json(cls, path):
        with open(str(path), encoding="utf-8") as file:
            obj = json.load(file, object_hook=to_nested_dataclass)
        return obj if isinstance(obj, cls) else None


### JSON


def is_dataclass_instance(obj):
    """Returns True if a class is an instance of a dataclass (and not a
    dataclass itself)
    """
    return dataclasses.is_dataclass(obj) and not isinstance(obj, type)


def as_nested_dict(obj):
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
        result = []
        for f in dataclasses.fields(obj):
            value = as_nested_dict(getattr(obj, f.name))  # recursive
            result.append((f.name, value))

        result.append(("__dataclass__", obj.__class__.__name__))
        return dict(result)

    elif isinstance(obj, Iterable):
        iter = (as_nested_dict(e) for e in obj)

        if isinstance(obj, list):
            return list(iter)
        if isinstance(obj, tuple):
            return tuple(iter)
        if isinstance(obj, dict):
            return {key: as_nested_dict(obj[key]) for key in obj}

    elif isinstance(obj, Enum):
        # https://stackoverflow.com/a/24482806
        return {"__enum__": str(obj)}
    return obj


class DataclassJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if is_dataclass_instance(o):
            return as_nested_dict(o)
        else:
            print(type(o))
        return super().default(o)


def to_nested_dataclass(obj):
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
        if class_ := obj.pop("__dataclass__", None):
            result = []
            for key in obj:
                value = to_nested_dataclass(obj[key])  # recursive
                result.append((key, value))
            return globals()[class_](**dict(result))
        elif "__enum__" in obj:
            # https://stackoverflow.com/a/24482806
            name, member = obj["__enum__"].split(".")
            if issubclass(class_ := globals()[name], Enum):
                return getattr(class_, member)
        else:
            return {key: to_nested_dataclass(obj[key]) for key in obj}

    elif isinstance(obj, Iterable):
        iter = (to_nested_dataclass(e) for e in obj)

        if isinstance(obj, list) or isinstance(obj, tuple):
            return tuple(iter)

    return obj


if __name__ == "__main__":
    import doctest

    doctest.testmod()
