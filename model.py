import enum
from itertools import combinations
from dataclasses import dataclass, field
from typing import Sequence, Set
import networkx as nx


class Direction(enum.Enum):
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

    Tuple of two Rooms will represent a connection between them.
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


@dataclass
class RoomNetwork:
    """Wraps networkx Graph of Rooms.

    >>> living_room = Room(element_id=0, name='거실', height=Length.from_ft(10))
    >>> kitchen = Room(element_id=1, name='주방', height=Length.from_ft(10))
    >>> bedroom = Room(element_id=2, name='침실', height=Length.from_ft(8))

    >>> g = nx.Graph([(living_room, kitchen), (living_room, bedroom)])
    >>> rn = RoomNetwork(g)
    >>> rn
    Room network with 3 rooms and 2 connections
    """

    graph: nx.Graph

    def __repr__(self):
        return (
            f"Room network with {self.graph.number_of_nodes()} rooms "
            f"and {self.graph.number_of_edges()} connections"
        )

    @classmethod
    def from_edges(cls, edge_list):
        G = nx.Graph()
        G.add_edges_from(edge_list)
        return cls(G)


@dataclass
class House:
    """Model of a house for the housing DNA analysis.

    >>> living_room = Room(element_id=0, name='거실', height=Length.from_ft(10))
    >>> kitchen = Room(element_id=1, name='주방', height=Length.from_ft(10))
    >>> bedroom = Room(element_id=2, name='침실', height=Length.from_ft(8))
    >>> rooms = [living_room, kitchen, bedroom]

    >>> conns = [(living_room, kitchen), (living_room, bedroom)]
    >>> rn = RoomNetwork(graph=nx.Graph(conns))

    >>> house = House(rooms=rooms, room_network=rn)
    >>> house  #doctest: +ELLIPSIS
    House(rooms=[Room(...),...], room_network=Room network with ...)
    """

    rooms: Sequence[Room]
    room_network: RoomNetwork

    # @classmethod
    # def from_json(cls, path):
    #     return cls()


if __name__ == "__main__":
    import doctest

    doctest.testmod()
