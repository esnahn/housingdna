if __name__ == "__main__" and __package__ is None:
    # set relative import path
    import sys, pathlib

    dir_level = 1

    assert dir_level >= 1
    package_path = pathlib.PurePath(__file__).parents[dir_level - 1]

    __package__ = package_path.name
    sys.path.append(str(package_path.parent))

from os import terminal_size
from .model import (
    Direction,
    House,
    Glazing,
    RevitObject,
    Room,
    Length,
    RoomConnection,
    RoomGlazingRelation,
    multiple_sides,
)

from pathlib import PurePath

# build mock.json

# room element_id start with 373 are "main rooms"
# ex) "373(생활공간:main rooms),376(부속실:sub rooms)+000"
# windows=[1,2,3,4]


rooms = (
    Room(element_id=373001, name="거실 1", height=Length(mm=4000.0)),
    Room(element_id=373002, name="침실 2", height=Length(mm=4000.0)),
    Room(element_id=376006, name="드레스룸 6", height=Length(mm=7600.0)),
    Room(element_id=376003, name="발코니 3", height=Length(mm=7600.0)),
)
conns = (
    RoomConnection(a_id=373002, b_id=376006, type_=RevitObject.DOOR),
    RoomConnection(a_id=373001, b_id=373002, type_=RevitObject.DOOR),
)
openings = (
    Glazing(1, RevitObject.WINDOW, True),
    Glazing(2, RevitObject.WINDOW, False),
    Glazing(3, RevitObject.WINDOW, True),
    Glazing(4, RevitObject.CURTAIN_WALL, True),
)

rels = (
    RoomGlazingRelation(373002, 2, (Direction.SOUTH,)),
    RoomGlazingRelation(373001, 3, (Direction.SOUTH,)),
    RoomGlazingRelation(376003, 1, (Direction.SOUTH,)),
    RoomGlazingRelation(376003, 2, (Direction.NORTH,)),
    RoomGlazingRelation(376006, 4, (Direction.NORTH, Direction.WEST)),
)


house = House(
    rooms=rooms, room_connections=conns, glazings=openings, room_glazing_relations=rels
)
house.to_json(PurePath(__file__).parent / "models/gomock.json")
print(House.from_json(PurePath(__file__).parent / "models/gomock.json"))
