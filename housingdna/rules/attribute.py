from typing import List, Mapping, Sequence
from .type import N

import numpy as np
from ..model import House, Room
from .name import is_main, judge_by_name


def dnas_attribute(
    model: House,
) -> List[N]:

    main_list = [room.element_id for room in model.rooms if is_main(room)]

    room_heights = {room.element_id: room.height.mm for room in model.rooms}

    dna: List[N] = []
    for key, eval in [
        ("dna56", dna56_higher_main(room_heights, main_list)),
    ]:
        if bool(eval) == True:
            dna.append(key)
    return dna


def is_mbr(room: Room) -> bool:
    # TODO: should include virtually main bedroom without these exact names.
    exact_list = ["안방", "부부 침실", "main bedroom", "master bedroom", "mbr"]
    return judge_by_name(room.name, exact_list)


def dna56_higher_main(
    heights: Mapping[int, float], main_list: Sequence[int]
) -> List[int]:
    """생활공간 중 다른 생활공간들보다 층고가 높은 (차이나는) 실이 있는지를 판단"""

    main_heights = {room: heights[room] for room in main_list}
    main_median: float = float(np.median(list(main_heights.values())))
    return [room for room, height in main_heights.items() if height > main_median]
