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
    Opening,
    RevitObject,
    Room,
    Length,
    RoomConnection,
    RoomOpeningRelation,
)

from pathlib import PurePath

# build mock.json
rooms = (
    Room(element_id=373987, name="거실 1", height=Length(mm=4000.0)),
    Room(element_id=373990, name="침실 2", height=Length(mm=4000.0)),
    Room(element_id=376804, name="드레스룸 6", height=Length(mm=7600.0)),
)
conns = (
    RoomConnection(a_id=373990, b_id=376804, type_=RevitObject.ROOM_SEPARATION_LINE),
    RoomConnection(a_id=373987, b_id=373990, type_=RevitObject.DOOR),
)
openings = (Opening(1, RevitObject.WINDOW, True),)
rels = (RoomOpeningRelation(373990, 1, Direction.SOUTH),)
house = House(
    rooms=rooms, room_connections=conns, openings=openings, room_opening_relations=rels
)
house.to_json(PurePath(__file__).parent / "models/mock.json")
print(House.from_json(PurePath(__file__).parent / "models/mock.json"))
