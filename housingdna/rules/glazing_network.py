from typing import List, Mapping

from ..model import (
    Direction, RevitObject,
    House,)
from .type import N
from .name import (
    is_ancillary,
    is_bedroom,
    is_main,
    is_semi_outdoor, is_corridor
)
import networkx as nx


def dnas_glazing_network(
    model: House,
) -> List[N]:
    # room-glazing network
    G: nx.DiGraph = nx.DiGraph()
    # assuming mid-latitude northern hemisphere
    sun_directions = [Direction.SOUTH,
                      Direction.SOUTHEAST, Direction.SOUTHWEST]
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
    sunlit_order: int = 3

    # dna40_northface를 위한 코드
    south = [(rel.room_id) for rel in model.room_glazing_relations if rel.room_id in main_list and any(
        (facing in sun_directions) for facing in rel.facings)]
    north = [(rel.room_id) for rel in model.room_glazing_relations if rel.room_id in indoor_ancill_list and any(
        (facing in opposite_directions) for facing in rel.facings)] + [room for room in indoor_ancill_list if sun_dict[room] > sunlit_order]

    # dna39_Light_dark_contrast를 위한 코드
    conn_types_open = [RevitObject.ROOM_SEPARATION_LINE]
    list_conn_values1 = [
        sun_dict[conn.a_id] for conn in model.room_connections if conn.type_ in conn_types_open]
    list_conn_values2 = [
        sun_dict[conn.b_id] for conn in model.room_connections if conn.type_ in conn_types_open]

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
        (
            "dna40",
            dna40_northface(sun_dict, indoor_ancill_list, south, north),
        ),
        (
            "dna39",
            dna39_Light_dark_contrast(list_conn_values1, list_conn_values2),
        ),
        ("dna43", dna43_fun_corr(model)),
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
            n: int = nx.shortest_path_length(
                sun_graph, room_id, glazing)  # type: ignore
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


# DONE: dna40_northface : 3번째 코딩 시도(코드 줄이기)... 성공!!
def dna40_northface(sun_dict: Mapping[int, int],
                    indoor_ancill_list: List[int],
                    south: List[int],
                    north: List[int],
                    ) -> List[int]:

    sunlit_order: int = 3  # consider it sunlit if order is up to 3 steps

    # 1. 채광 필요가 공간들이 남쪽에
    # 2. 채광 필요가 적은 공간이 북쪽에
    return [room for room in south if sun_dict[room] <= sunlit_order] + [room for room in north if sun_dict[room] >
                                                                         sunlit_order]+[room for room in indoor_ancill_list if room not in House.room_glazing_relations]

# DONE: dna39_Light_dark_contrast: 성공!!


def dna39_Light_dark_contrast(list_conn_values1: List[int],
                              list_conn_values2: List[int],
                              ) -> List[int]:
    if list_conn_values1 != list_conn_values2:  # 오픈으로 연결된 방들의 채광정도의 차이가 있는 경우, True
        return True
    return False


def dna43_fun_corr(
    model: House,
) -> List[N]:
    # room-glazing network
    conn_types_open = [RevitObject.ROOM_SEPARATION_LINE]
    conn_types_win = [RevitObject.WINDOW, RevitObject.CURTAIN_WALL]
    glazing_types = [(gla.element_id)
                     for gla in model.glazings if gla.type_ in conn_types_win]
    # 외기에 면한 창 리스트
    outmost_list = [g.element_id for g in model.glazings if g.outmost]
    # 외기에 면한 방 리스트
    outmost_room = [(out.room_id)
                    for out in model.room_glazing_relations if out.room_id in model.rooms and out.glazing_id in outmost_list]

    corr_list = [
        room.element_id for room in model.rooms if is_corridor(room)]
    ancill_list = [
        room.element_id for room in model.rooms if is_ancillary(room)]
    # 1. 복도가 없을 때
    fun_corr1 = [room for room in corr_list]
    # 2. 복도가 있을 때, 복도와 연결된 다른 공간이 오픈되어 있는 경우. but 현관과 복도 오픈 연결은 제외
    fun_corr2 = [
        (conn.a_id, conn.type_) for conn in model.room_connections if conn.a_id in corr_list and conn.type_ in conn_types_open and not ancill_list] + [
        (conn.b_id, conn.type_) for conn in model.room_connections if conn.b_id in corr_list and conn.type_ in conn_types_open and not ancill_list]
    # 3. 복도가 있을 때, 복도에 외기로의 창이 있는 경우. 외기에 면한 창만을 어떻게 설정????
    fun_corr3 = [rel for rel in outmost_room if rel in corr_list]

    # return fun_corr1, fun_corr2, fun_corr3, outmost_room

    if bool(fun_corr1) == False or bool(fun_corr2 or fun_corr3) == True:
        return True
