from typing import List, Mapping

from ..model import (
    Direction,
    House,
)
from .type import N
from .name import (
    is_ancillary,
    is_bedroom,
    is_main,
    is_semi_outdoor,
)
import networkx as nx


def dnas_glazing_network(
    model: House,
) -> List[N]:
    # room-glazing network
    G: nx.DiGraph = nx.DiGraph()
    # assuming mid-latitude northern hemisphere
    sun_directions = [Direction.SOUTH, Direction.SOUTHEAST, Direction.SOUTHWEST]
    opposite_directions = [d.opposite() for d in sun_directions]
    edges = [
        (rel.room_id, rel.glazing_id)
        for rel in model.room_glazing_relations
        if any((facing in sun_directions) for facing in rel.facings)
    ] + [
        (rel.glazing_id, rel.room_id)
        for rel in model.room_glazing_relations
        if any((facing in opposite_directions) for facing in rel.facings)
    ]
    G.add_edges_from(edges)

    main_list = [room.element_id for room in model.rooms if is_main(room)]
    bed_list = [room.element_id for room in model.rooms if is_bedroom(room)]
    indoor_ancill_list = [
        room.element_id
        for room in model.rooms
        if is_ancillary(room) and not is_semi_outdoor(room)
    ]

    outmost_list = [g.element_id for g in model.glazings if g.outmost]

    sun_dict = {
        room.element_id: analyze_sun_order(G, outmost_list, room.element_id)
        for room in model.rooms
    }

    dna: List[N] = []
    for key, eval in [
        (
            "dna37",
            dna37_indoor_for_sunlight(sun_dict, main_list, indoor_ancill_list),
        ),
        (
            "dna52",
            dna52_bedroom_for_sunlight(sun_dict, bed_list),
        ),
    ]:
        if bool(eval) == True:
            dna.append(key)

    # # opposite dna
    # for a, not_a in [
    #     ("dna38", "dna38-1"),
    # ]:
    #     if not a in dna:
    #         dna.append(not_a)
    return dna


def analyze_sun_order(
    sun_graph: nx.DiGraph,
    outmost_list: List[int],
    room_id: int,
    max_order: int = 9,  # 9 steps from outdoor is as dark as it gets
) -> int:
    min_order = max_order
    for glazing in outmost_list:
        try:
            n: int = nx.shortest_path_length(sun_graph, room_id, glazing)  # type: ignore
            if n < min_order:
                min_order = n
        except nx.NodeNotFound:
            # 창이 없어서 방 노드가 안 만들어진 경우
            pass
        except nx.NetworkXNoPath:
            # 여기는 경로가 없는 경우
            pass
    return min_order


def dna37_indoor_for_sunlight(
    sun_dict: Mapping[int, int],
    main_list: List[int],
    indoor_ancill_list: List[int],
) -> List[int]:
    sun_main = {room: sun_dict[room] for room in main_list}
    sun_ancill = {room: sun_dict[room] for room in indoor_ancill_list}
    avg_sun_main = sum(sun_main.values()) / len(sun_main.values())
    avg_sun_ancill = sum(sun_ancill.values()) / len(sun_ancill.values())

    # if main rooms are close to sunlight than (indoor) ancillary rooms
    if avg_sun_main < avg_sun_ancill:
        return [  # main rooms that are close to sunlight than an average ancillary room
            room for room, sun_order in sun_main.items() if sun_order < avg_sun_ancill
        ] + [  # ancillary rooms that are far from sunlight than an average main room
            room for room, sun_order in sun_ancill.items() if sun_order > avg_sun_main
        ]
    else:
        return []


def dna52_bedroom_for_sunlight(
    sun_dict: Mapping[int, int], bed_list: List[int]
) -> List[int]:
    sunlit_order: int = 3  # consider it sunlit if order is up to 3 steps

    return [room for room in bed_list if sun_dict[room] <= sunlit_order]
