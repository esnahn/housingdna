from .model import *

rooms = [
    Room(element_id=373987, name="거실 1", height=Length(mm=4000.0)),
    Room(element_id=373990, name="침실 2", height=Length(mm=4000.0)),
    Room(element_id=376804, name="드레스룸 6", height=Length(mm=7600.0)),
]

room_network = RoomNetwork.from_edges(
    [
        (
            Room(element_id=373990, name="침실 2", height=Length(mm=4000.0)),
            Room(element_id=376804, name="드레스룸 6", height=Length(mm=7600.0)),
        ),
        (
            Room(element_id=373990, name="침실 2", height=Length(mm=4000.0)),
            Room(element_id=373987, name="거실 1", height=Length(mm=4000.0)),
        ),
    ]
)


def get_model(path):
    return House(
        rooms=rooms,
        room_network=room_network,
    )
