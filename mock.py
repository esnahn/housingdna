if __name__ == "__main__" and __package__ is None:
    # set relative import path
    import sys, pathlib

    dir_level = 1

    assert dir_level >= 1
    package_path = pathlib.PurePath(__file__).parents[dir_level - 1]

    __package__ = package_path.name
    sys.path.append(str(package_path.parent))

from .model import House


def get_model(path):
    return House.from_json(path)


if __name__ == "__main__":
    from .model import Room, Length

    from pathlib import PurePath

    # build mock.json
    rooms = (
        Room(element_id=373987, name="거실 1", height=Length(mm=4000.0)),
        Room(element_id=373990, name="침실 2", height=Length(mm=4000.0)),
        Room(element_id=376804, name="드레스룸 6", height=Length(mm=7600.0)),
    )
    conns = (
        (373990, 376804),
        (373990, 373987),
    )
    house = House(
        rooms=rooms,
        room_connections=conns,
    )
    house.to_json(PurePath(__file__).parent / "models/mock.json")
    print(House.from_json(PurePath(__file__).parent / "models/mock.json"))
