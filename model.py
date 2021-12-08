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
    mm: float

    def __post_init__(self):
        # limits the precision
        object.__setattr__(self, "mm", round(self.mm, 2))

    @classmethod
    def from_ft(cls, val_in_feet):
        return cls(val_in_feet * 304.8)


@dataclass(frozen=True)
class Room:
    element_id: int
    name: str = field(compare=False)
    height: Length = field(compare=False)


@dataclass(frozen=True)
class RoomNetwork:
    graph: nx.Graph = field(repr=False)  # mutable obscure object; no show on repr

    @classmethod
    def from_edges(cls, edge_list):
        G = nx.Graph()
        G.add_edges_from(edge_list)
        return cls(G)


@dataclass(frozen=True)
class House:
    rooms: Sequence[Room]
    room_network: RoomNetwork


if __name__ == "__main__":
    print(Length(10))
    print(Length.from_ft(10))

    print(Room(0, "거실", Length.from_ft(30)))

    a = Room(0, "거실", Length.from_ft(30))
    b = Room(0, "침실", Length.from_ft(25))
    assert a == b  # compare id only
    assert id(a) != id(b)  # different objects
    {a: b}  # can be key

    c = (a, a)
    d = (b, b)
    assert c == d  # same (eq) room, same connection
    assert len(set([c, d])) == 1  # same connection, so only 1 connection remains

    g = nx.Graph([c])
    n = RoomNetwork(g)
    print(n.graph)

    x = Room(-1, "현관", Length.from_ft(15))
    try:
        # even pylance finds a problem
        n.graph = nx.Graph([d])  # type: ignore
    except Exception as e:
        print(e)  # no change!
    n.graph.add_edge(a, x)  # graph var is mutable
    print(n.graph)

if __name__ == "__main__":
    import doctest

    doctest.testmod()
