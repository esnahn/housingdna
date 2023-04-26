from typing import Dict, List, Mapping, Sequence, Set
from .type import N

import housingdna.file as hdna
import numpy as np
from ..model import (
    Direction,
    Glazing,
    House,
    RevitObject,
    Room,
    RoomGlazingRelation,
    multiple_sides,
)
from .name import (
    is_main,
    is_semi_outdoor,)
from .name import is_main, judge_by_name


def dnas_attribute(
    model: House,
) -> List[N]:

    main_list = [room.element_id for room in model.rooms if is_main(room)]

    room_heights = {room.element_id: room.height.mm for room in model.rooms}

    outmost_list = [g.element_id for g in model.glazings if g.outmost]

    semi_out_list = [
        room.element_id for room in model.rooms if is_semi_outdoor(room)]

    dna: List[N] = []
    for key, eval in [
        ("dna55", dna55_higher_main(room_heights, main_list)),
        ("dna61", dna61_windows_on_two_sides(
            model.room_glazing_relations, semi_out_list)),
        ("dna64", dna64_window_to_outdoor(
            model.room_glazing_relations, outmost_list)),
        ("dna68", dna68_window_interior(model.glazings, model.room_glazing_relations)),
    ]:
        if bool(eval) == True:
            dna.append(key)
    return dna


def is_mbr(room: Room) -> bool:
    # TODO: should include virtually main bedroom without these exact names.
    exact_list = ["안방", "부부 침실", "main bedroom", "master bedroom", "mbr"]
    return judge_by_name(room.name, exact_list)


def dna55_higher_main(
    heights: Mapping[int, float], main_list: Sequence[int]
) -> List[int]:
    """생활공간 중 다른 생활공간들보다 층고가 높은 (차이나는) 실이 있는지를 판단"""

    main_heights = {room: heights[room] for room in main_list}
    main_median: float = float(np.median(list(main_heights.values())))
    return [room for room, height in main_heights.items() if height > main_median]


def dna61_windows_on_two_sides(rels: Sequence[RoomGlazingRelation], outmost_list: List[int]) -> List[int]:
    room_facings: Dict[int, Set[Direction]] = dict()
    for rel in rels:
        room_facings.setdefault(rel.room_id, set()).update(rel.facings)
    return [room for room, facings in room_facings.items() if multiple_sides(facings) and not outmost_list]


def dna64_window_to_outdoor(
    rels: Sequence[RoomGlazingRelation], outmost_list: List[int]
) -> List[int]:
    return [rel.room_id for rel in rels if rel.glazing_id in outmost_list]


def dna68_window_interior(
    glazings: Sequence[Glazing], rels: Sequence[RoomGlazingRelation]
) -> List[int]:
    # windows, curtain walls, and glass doors
    # between rooms (not at the outmost boundary of the house)
    # excluding imaginary separation lines
    inner_window_list = [
        g.element_id
        for g in glazings
        if (not g.outmost) and g.type_ != RevitObject.ROOM_SEPARATION_LINE
    ]
    window_facings: Dict[int, Set[Direction]] = dict()
    for rel in rels:
        if rel.glazing_id in inner_window_list:
            window_facings.setdefault(
                rel.glazing_id, set()).update(rel.facings)
    real_inner_window_list = [
        window for window, facings in window_facings.items() if multiple_sides(facings)
    ]
    return [rel.room_id for rel in rels if rel.glazing_id in real_inner_window_list]
