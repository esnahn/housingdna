if __name__ == "__main__" and __package__ is None:
    # set relative import path
    import sys
    import pathlib

    dir_level = 2

    assert dir_level >= 1
    file_path = pathlib.PurePath(__file__)
    sys.path.append(str(file_path.parents[dir_level]))

    package_path = ""
    for level in range(dir_level - 1, 0 - 1, -1):
        package_path += file_path.parents[level].name
        if level > 0:
            package_path += "."
    __package__ = package_path


import networkx as nx
import housingdna.file as hdna
from itertools import chain
from typing import List, Tuple, Dict, Mapping, Sequence, Set
from ..model import (
    House,
    RevitObject,
    Glazing,
    Direction,
    Room,
    RoomGlazingRelation,
    multiple_sides,
)
from .type import N, E, A
from .nodes import node_names
from .edges import white_edges, gray_edges
from .name import (
    dna34_ent_transition,
    dna33_main_entrance,
    is_main,
    dnas_room_name,
    is_bedroom,
    is_kitchen,
    is_semi_outdoor,
    is_entrance,
    is_dining,
    is_bathroom,
    is_storage,
    is_dressroom,
    is_corridor,
    is_public,
    is_ancillary,
    is_living,
    is_semi_outdoor,
)
from .attribute import is_mbr, dnas_attribute, room_outmost_win_count
from .room_network import (
    dnas_room_network,
    dna36_pub_priv_gradient,
    dna38_direct_connection,
    dna41_central_public,
    dna44_couples_realm,
    dna45_childrens_realm,
)
from .glazing_network import (
    dnas_glazing_network,
    dna37_indoor_for_sunlight,
    dna52_bedroom_for_sunlight,
)
from housingdna.rules import edges


# 분석 대상 불러오기: revit file 명 ""에 추가할 것
test_model = hdna.get_model("housingdna/models/Korea_01_위례자연앤셑트럴자이_98.79(완성).json")

# test_model = hdna.get_model(
#     "housingdna/models/Japan_01_Sato Kogyo Co._81.58(수정).json"
# )
# test_model = hdna.get_model(
#     "housingdna/models/China_01_2013_119.37(완성)_test2.json"
# )
# print(test_model)

# 네트워크 만들기
# G = nx.Graph()
# G.add_edges_from((conn.a_id, conn.b_id)
#                  for conn in test_model.room_connections)
# list(G.edges)

# list_edges = [G.edges]
# print(list_edges)


def dnas_obvious(model: House) -> List[N]:
    dna: List[N] = []
    for key, eval in [("dna1", dna1_is_house(model))]:
        if bool(eval) == True:
            dna.append(key)
    return dna


def dna1_is_house(model: House) -> List[int]:
    # Every house is a house
    # return a list of ids of every rooms
    return [room.element_id for room in model.rooms]


# print(list_housing_nodes(test_model))


# 도출되는 노드 리스트
node_ids_2: List[N] = list(
    chain(
        dnas_obvious(test_model),
        dnas_room_name(test_model),
        dnas_attribute(test_model),
        dnas_room_network(test_model),
        dnas_glazing_network(test_model),
    )
)

# print(node_ids_2)

# 공간 분류 리스트 정리
rooms = [room.element_id for room in test_model.rooms]
pub_list = [room.element_id for room in test_model.rooms if is_public(room)]
mbr_list = [room.element_id for room in test_model.rooms if is_mbr(room)]
ancill_list = [room.element_id for room in test_model.rooms if is_ancillary(room)]
semi_out_list = [room.element_id for room in test_model.rooms if is_semi_outdoor(room)]
ent_list = [room.element_id for room in test_model.rooms if is_entrance(room)]
living_list = [room.element_id for room in test_model.rooms if is_living(room)]
dining_list = [room.element_id for room in test_model.rooms if is_dining(room)]
kit_list = [room.element_id for room in test_model.rooms if is_kitchen(room)]
bath_list = [room.element_id for room in test_model.rooms if is_bathroom(room)]
sto_list = [room.element_id for room in test_model.rooms if is_storage(room)]
dress_list = [room.element_id for room in test_model.rooms if is_dressroom(room)]
corr_list = [room.element_id for room in test_model.rooms if is_corridor(room)]
bed_list = [room.element_id for room in test_model.rooms if is_bedroom(room)]
living_list = [room.element_id for room in test_model.rooms if is_living(room)]
main_list = [room.element_id for room in test_model.rooms if is_main(room)]
indoor_ancill_list = [
    room.element_id
    for room in test_model.rooms
    if is_ancillary(room) and not is_semi_outdoor(room)
]
bedonly_list = list(set(bed_list) - set(mbr_list))
sun_directions = [
    Direction.SOUTH,
    Direction.EAST,
    Direction.SOUTHEAST,
    Direction.SOUTHWEST,
]
opposite_directions = [d.opposite() for d in sun_directions]
# print(semi_out_list)

# print(main_list)


def gray_edges_list(
    model: House,
) -> List[Tuple[N, A]]:
    node_ids: List[N] = list(
        chain(
            edge_name_1_1(test_model),
            edge_name_1_2(test_model),
            edge_name_2_1(test_model),
        )
    )
    return node_ids


def edge_name_1_1(
    model: House,
) -> List[Tuple[N, A]]:
    node_ids: List[N] = list(
        chain(
            dna36_dna46(test_model),
            dna36_dna47(test_model),
            dna36_dna48(test_model),
            dna36_dna51(test_model),
        )
    )
    return node_ids


def edge_name_1_2(
    model: House,
) -> List[Tuple[N, A]]:
    node_ids: List[N] = list(
        chain(
            dna40_dna41(test_model),
            dna40_dna44(test_model),
            dna40_dna45(test_model),
            dna40_dna46(test_model),
            dna40_dna47(test_model),
            dna40_dna48(test_model),
            dna40_dna49(test_model),
            dna40_dna51(test_model),
        )
    )
    return node_ids


def edge_name_2_1(
    model: House,
) -> List[Tuple[N, A]]:
    node_ids: List[N] = list(
        chain(
            dna42_dna48(test_model),
            dna42_dna49(test_model),
            dna46_dna48(test_model),
            dna46_dna49(test_model),
            dna51_dna48(test_model),
        )
    )
    return node_ids


def edge_name_2_2(
    model: House,
) -> List[Tuple[N, A]]:
    node_ids: List[N] = list(
        chain(
            dna41_dna43(test_model),
            dna41_dna46(test_model),
            dna41_dna47(test_model),
            dna44_dna48(test_model),
            dna44_dna49(test_model),
            dna44_dna51(test_model),
            dna45_dna48(test_model),
            dna45_dna49(test_model),
            dna45_dna51(test_model),
        )
    )
    return node_ids


# def edge_name_4_1(
#     model: House,
# ) -> List[Tuple[N, A]]:
#     node_ids: List[N] = list(
#         chain(
#             dna42_dna61(test_model),
#             dna42_dna64(test_model),
#             dna42_dna67(test_model),
#             dna42_dna68(test_model),
#             dna43_dna61(test_model),
#             dna43_dna64(test_model),
#             dna43_dna67(test_model),
#             dna43_dna68(test_model),
#             dna46_dna61(test_model),
#             dna46_dna64(test_model),
#             dna46_dna67(test_model),
#             dna46_dna68(test_model),
#             dna46_dna69(test_model),
#             dna47_dna61(test_model),
#             dna47_dna64(test_model),
#             dna47_dna67(test_model),
#             dna47_dna68(test_model),
#             dna47_dna69(test_model),
#             dna48_dna61(test_model),
#             dna48_dna64(test_model),
#             dna48_dna67(test_model),
#             dna48_dna68(test_model),
#             dna48_dna69(test_model),
#             dna49_dna64(test_model),
#             dna49_dna69(test_model),
#             dna51_dna61(test_model),
#             dna51_dna64(test_model),
#             dna51_dna69(test_model),
#         )
#     )
#     return node_ids


def edge_name_6(
    model: House,
) -> List[Tuple[N, A]]:
    node_ids: List[N] = list(
        chain(
            dna44_dna29(test_model),
            dna45_dna29(test_model),
            dna46_dna29(test_model),
            dna47_dna29(test_model),
        )
    )
    return node_ids


# edge name 1_1


def dna36_dna46(
    model: House,
) -> List[Tuple[E, A]]:
    edge = [
        ((a, b), {})
        for a in node_ids_2
        if a in "dna36"
        for b in node_ids_2
        if b in "dna46"
    ]
    if bool(edge) == True:
        return [("dna36", "dna46")]
    else:
        return []


def dna36_dna47(
    model: House,
) -> List[Tuple[E, A]]:
    edge = [
        ((a, b), {})
        for a in node_ids_2
        if a in "dna36"
        for b in node_ids_2
        if b in "dna47"
    ]
    if bool(edge) == True:
        return [("dna36", "dna47")]
    else:
        return []


def dna36_dna48(
    model: House,
) -> List[Tuple[E, A]]:
    edge = [
        ((a, b), {})
        for a in node_ids_2
        if a in "dna36"
        for b in node_ids_2
        if b in "dna48"
    ]
    if bool(edge) == True:
        return [("dna36", "dna48")]
    else:
        return []


def dna36_dna51(
    model: House,
) -> List[Tuple[E, A]]:
    edge = [
        ((a, b), {})
        for a in node_ids_2
        if a in "dna36"
        for b in node_ids_2
        if b in "dna51"
    ]
    if bool(edge) == True:
        return [("dna36", "dna51")]
    else:
        return []


# edge name 1_2 채광 필요가 적은 공간과 채광이 중요한 공간으로 구분


def dna40_dna41(
    model: House,
) -> List[Tuple[E, A]]:
    edge = [
        ((a, b), {})
        for a in node_ids_2
        if a in "dna40"
        for b in node_ids_2
        if b in "dna41"
    ]
    south = [
        (rel.room_id)
        for rel in test_model.room_glazing_relations
        if rel.room_id in main_list
        and any((facing in sun_directions) for facing in rel.facings)
    ]
    if bool(edge) == True and bool(south) == True:
        return [("dna40", "dna41")]
    else:
        return []


def dna40_dna44(
    model: House,
) -> List[Tuple[E, A]]:
    edge = [
        ((a, b), {})
        for a in node_ids_2
        if a in "dna40"
        for b in node_ids_2
        if b in "dna44"
    ]
    south = [
        (rel.room_id)
        for rel in test_model.room_glazing_relations
        if rel.room_id in mbr_list
        and any((facing in sun_directions) for facing in rel.facings)
    ]
    if bool(edge) == True and bool(south) == True:
        return [("dna40", "dna44")]
    else:
        return []


def dna40_dna45(
    model: House,
) -> List[Tuple[E, A]]:
    edge = [
        ((a, b), {})
        for a in node_ids_2
        if a in "dna40"
        for b in node_ids_2
        if b in "dna45"
    ]
    south = [
        (rel.room_id)
        for rel in test_model.room_glazing_relations
        if rel.room_id in bedonly_list
        and any((facing in sun_directions) for facing in rel.facings)
    ]
    if bool(edge) == True and bool(south) == True:
        return [("dna40", "dna45")]
    else:
        return []


def dna40_dna46(
    model: House,
) -> List[Tuple[E, A]]:
    edge = [
        ((a, b), {})
        for a in node_ids_2
        if a in "dna40"
        for b in node_ids_2
        if b in "dna46"
    ]
    south = [
        (rel.room_id)
        for rel in test_model.room_glazing_relations
        if rel.room_id in kit_list
        and any((facing in sun_directions) for facing in rel.facings)
    ]
    if bool(edge and south) == True:
        return [("dna40", "dna46")]
    else:
        return []


def dna40_dna47(
    model: House,
) -> List[Tuple[E, A]]:
    edge = [
        ((a, b), {})
        for a in node_ids_2
        if a in "dna40"
        for b in node_ids_2
        if b in "dna47"
    ]
    south = [
        (rel.room_id)
        for rel in test_model.room_glazing_relations
        if rel.room_id in dining_list
        and any((facing in sun_directions) for facing in rel.facings)
    ]
    if bool(edge and south) == True:
        return [("dna40", "dna47")]
    else:
        return []


def dna40_dna48(
    model: House,
) -> List[Tuple[E, A]]:
    edge = [
        ((a, b), {})
        for a in node_ids_2
        if a in "dna40"
        for b in node_ids_2
        if b in "dna48"
    ]
    north = [
        (rel.room_id)
        for rel in test_model.room_glazing_relations
        if rel.room_id in bath_list
        and any((facing in opposite_directions) for facing in rel.facings)
    ]
    if bool(edge and north) == True:
        return [("dna40", "dna48")]
    else:
        return []


def dna40_dna49(
    model: House,
) -> List[Tuple[E, A]]:
    edge = [
        ((a, b), {})
        for a in node_ids_2
        if a in "dna40"
        for b in node_ids_2
        if b in "dna49"
    ]
    north = [
        (rel.room_id)
        for rel in test_model.room_glazing_relations
        if rel.room_id in sto_list
        and any((facing in opposite_directions) for facing in rel.facings)
    ]
    if bool(edge and north) == True:
        return [("dna40", "dna49")]
    else:
        return []


def dna40_dna51(
    model: House,
) -> List[Tuple[E, A]]:
    edge = [
        ((a, b), {})
        for a in node_ids_2
        if a in "dna40"
        for b in node_ids_2
        if b in "dna51"
    ]
    north = [
        (rel.room_id)
        for rel in test_model.room_glazing_relations
        if rel.room_id in dress_list
        and any((facing in opposite_directions) for facing in rel.facings)
    ]
    if bool(edge and north) == True:
        return [("dna40", "dna51")]
    else:
        return []


# edge_name_2_1
def dna42_dna48(
    model: House,
) -> List[Tuple[E, A]]:
    edge = [
        ((a, b), {})
        for a in node_ids_2
        if a in "dna42"
        for b in node_ids_2
        if b in "dna48"
    ]
    conn_logic = [
        (conn.a_id, conn.b_id)
        for conn in test_model.room_connections
        if conn.a_id in ent_list and conn.b_id in bath_list
    ] + [
        (conn.a_id, conn.b_id)
        for conn in test_model.room_connections
        if conn.a_id in bath_list and conn.b_id in ent_list
    ]
    if bool(edge and conn_logic) == True:
        return [("dna42", "dna48")]
    else:
        return []


def dna42_dna49(
    model: House,
) -> List[Tuple[E, A]]:
    edge = [
        ((a, b), {})
        for a in node_ids_2
        if a in "dna42"
        for b in node_ids_2
        if b in "dna49"
    ]
    conn_logic = [
        (conn.a_id, conn.b_id)
        for conn in test_model.room_connections
        if conn.a_id in ent_list and conn.b_id in sto_list
    ] + [
        (conn.a_id, conn.b_id)
        for conn in test_model.room_connections
        if conn.a_id in sto_list and conn.b_id in ent_list
    ]
    if bool(edge and conn_logic) == True:
        return [("dna42", "dna49")]
    else:
        return []


def dna46_dna48(
    model: House,
) -> List[Tuple[E, A]]:
    edge = [
        ((a, b), {})
        for a in node_ids_2
        if a in "dna46"
        for b in node_ids_2
        if b in "dna48"
    ]
    conn_logic = [
        (conn.a_id, conn.b_id)
        for conn in test_model.room_connections
        if conn.a_id in kit_list and conn.b_id in bath_list
    ] + [
        (conn.a_id, conn.b_id)
        for conn in test_model.room_connections
        if conn.a_id in bath_list and conn.b_id in kit_list
    ]
    if bool(edge and conn_logic) == True:
        return [("dna46", "dna48")]
    else:
        return []


def dna46_dna49(
    model: House,
) -> List[Tuple[E, A]]:
    edge = [
        ((a, b), {})
        for a in node_ids_2
        if a in "dna46"
        for b in node_ids_2
        if b in "dna49"
    ]
    conn_logic = [
        (conn.a_id, conn.b_id)
        for conn in test_model.room_connections
        if conn.a_id in kit_list and conn.b_id in sto_list
    ] + [
        (conn.a_id, conn.b_id)
        for conn in test_model.room_connections
        if conn.a_id in sto_list and conn.b_id in kit_list
    ]
    if bool(edge and conn_logic) == True:
        return [("dna46", "dna49")]
    else:
        return []


def dna51_dna48(
    model: House,
) -> List[Tuple[E, A]]:
    edge = [
        ((a, b), {})
        for a in node_ids_2
        if a in "dna51"
        for b in node_ids_2
        if b in "dna48"
    ]
    conn_logic = [
        (conn.a_id, conn.b_id)
        for conn in test_model.room_connections
        if conn.a_id in dress_list and conn.b_id in bath_list
    ] + [
        (conn.a_id, conn.b_id)
        for conn in test_model.room_connections
        if conn.a_id in bath_list and conn.b_id in dress_list
    ]
    if bool(edge and conn_logic) == True:
        return [("dna51", "dna48")]
    else:
        return []


# edge_name_2_2
def dna41_dna43(
    model: House,
) -> List[Tuple[E, A]]:
    edge = [
        ((a, b), {})
        for a in node_ids_2
        if a in "dna41"
        for b in node_ids_2
        if b in "dna43"
    ]
    conn_logic = [
        (conn.a_id, conn.b_id)
        for conn in test_model.room_connections
        if conn.a_id in living_list and conn.b_id in corr_list
    ] + [
        (conn.a_id, conn.b_id)
        for conn in test_model.room_connections
        if conn.a_id in corr_list and conn.b_id in pub_list and not living_list
    ]
    if bool(edge and conn_logic) == True:
        return [("dna41", "dna43")]
    else:
        return []


def dna41_dna46(
    model: House,
) -> List[Tuple[E, A]]:
    edge = [
        ((a, b), {})
        for a in node_ids_2
        if a in "dna41"
        for b in node_ids_2
        if b in "dna46"
    ]
    conn_logic = [
        (conn.a_id, conn.b_id)
        for conn in test_model.room_connections
        if conn.a_id in living_list and conn.b_id in kit_list
    ] + [
        (conn.a_id, conn.b_id)
        for conn in test_model.room_connections
        if conn.a_id in kit_list and conn.b_id in living_list
    ]
    if bool(edge and conn_logic) == True:
        return [("dna41", "dna46")]
    else:
        return []


def dna41_dna47(
    model: House,
) -> List[Tuple[E, A]]:
    edge = [
        ((a, b), {})
        for a in node_ids_2
        if a in "dna41"
        for b in node_ids_2
        if b in "dna47"
    ]
    conn_logic = [
        (conn.a_id, conn.b_id)
        for conn in test_model.room_connections
        if conn.a_id in living_list and conn.b_id in dining_list
    ] + [
        (conn.a_id, conn.b_id)
        for conn in test_model.room_connections
        if conn.a_id in dining_list and conn.b_id in living_list
    ]
    if bool(edge and conn_logic) == True:
        return [("dna41", "dna47")]
    else:
        return []


def dna44_dna48(
    model: House,
) -> List[Tuple[E, A]]:
    edge = [
        ((a, b), {})
        for a in node_ids_2
        if a in "dna44"
        for b in node_ids_2
        if b in "dna48"
    ]
    conn_logic = [
        (conn.a_id, conn.b_id)
        for conn in test_model.room_connections
        if conn.a_id in mbr_list and conn.b_id in bath_list
    ] + [
        (conn.a_id, conn.b_id)
        for conn in test_model.room_connections
        if conn.a_id in bath_list and conn.b_id in mbr_list
    ]
    if bool(edge and conn_logic) == True:
        return [("dna44", "dna48")]
    else:
        return []


def dna44_dna49(
    model: House,
) -> List[Tuple[E, A]]:
    edge = [
        ((a, b), {})
        for a in node_ids_2
        if a in "dna44"
        for b in node_ids_2
        if b in "dna49"
    ]
    conn_logic = [
        (conn.a_id, conn.b_id)
        for conn in test_model.room_connections
        if conn.a_id in mbr_list and conn.b_id in sto_list
    ] + [
        (conn.a_id, conn.b_id)
        for conn in test_model.room_connections
        if conn.a_id in sto_list and conn.b_id in mbr_list
    ]
    if bool(edge and conn_logic) == True:
        return [("dna44", "dna49")]
    else:
        return []


def dna44_dna51(
    model: House,
) -> List[Tuple[E, A]]:
    edge = [
        ((a, b), {})
        for a in node_ids_2
        if a in "dna44"
        for b in node_ids_2
        if b in "dna51"
    ]
    conn_logic = [
        (conn.a_id, conn.b_id)
        for conn in test_model.room_connections
        if conn.a_id in mbr_list and conn.b_id in dress_list
    ] + [
        (conn.a_id, conn.b_id)
        for conn in test_model.room_connections
        if conn.a_id in dress_list and conn.b_id in mbr_list
    ]
    if bool(edge and conn_logic) == True:
        return [("dna44", "dna51")]
    else:
        return []


def dna45_dna48(
    model: House,
) -> List[Tuple[E, A]]:
    edge = [
        ((a, b), {})
        for a in node_ids_2
        if a in "dna45"
        for b in node_ids_2
        if b in "dna48"
    ]
    conn_logic = [
        (conn.a_id, conn.b_id)
        for conn in test_model.room_connections
        if conn.a_id in bedonly_list and conn.b_id in bath_list
    ] + [
        (conn.a_id, conn.b_id)
        for conn in test_model.room_connections
        if conn.a_id in bath_list and conn.b_id in bedonly_list
    ]
    if bool(edge and conn_logic) == True:
        return [("dna45", "dna48")]
    else:
        return []


def dna45_dna49(
    model: House,
) -> List[Tuple[E, A]]:
    edge = [
        ((a, b), {})
        for a in node_ids_2
        if a in "dna45"
        for b in node_ids_2
        if b in "dna49"
    ]
    conn_logic = [
        (conn.a_id, conn.b_id)
        for conn in test_model.room_connections
        if conn.a_id in bedonly_list and conn.b_id in sto_list
    ] + [
        (conn.a_id, conn.b_id)
        for conn in test_model.room_connections
        if conn.a_id in sto_list and conn.b_id in bedonly_list
    ]
    if bool(edge and conn_logic) == True:
        return [("dna45", "dna49")]
    else:
        return []


def dna45_dna51(
    model: House,
) -> List[Tuple[E, A]]:
    edge = [
        ((a, b), {})
        for a in node_ids_2
        if a in "dna45"
        for b in node_ids_2
        if b in "dna51"
    ]
    conn_logic = [
        (conn.a_id, conn.b_id)
        for conn in test_model.room_connections
        if conn.a_id in bedonly_list and conn.b_id in dress_list
    ] + [
        (conn.a_id, conn.b_id)
        for conn in test_model.room_connections
        if conn.a_id in dress_list and conn.b_id in bedonly_list
    ]
    if bool(edge and conn_logic) == True:
        return [("dna45", "dna51")]
    else:
        return []


# edge_name_6


def dna44_dna29(
    model: House,
) -> List[Tuple[E, A]]:
    edge = [
        ((a, b), {})
        for a in node_ids_2
        if a in "dna44"
        for b in node_ids_2
        if b in "dna29"
    ]
    conn_logic = [
        (conn.a_id, conn.b_id)
        for conn in test_model.room_connections
        if conn.a_id in mbr_list and conn.b_id in semi_out_list
    ] + [
        (conn.a_id, conn.b_id)
        for conn in test_model.room_connections
        if conn.a_id in semi_out_list and conn.b_id in mbr_list
    ]
    if bool(edge and conn_logic) == True:
        return [("dna44", "dna29")]
    else:
        return []


def dna45_dna29(
    model: House,
) -> List[Tuple[E, A]]:
    edge = [
        ((a, b), {})
        for a in node_ids_2
        if a in "dna45"
        for b in node_ids_2
        if b in "dna29"
    ]
    conn_logic = [
        (conn.a_id, conn.b_id)
        for conn in test_model.room_connections
        if conn.a_id in bedonly_list and conn.b_id in semi_out_list
    ] + [
        (conn.a_id, conn.b_id)
        for conn in test_model.room_connections
        if conn.a_id in semi_out_list and conn.b_id in bedonly_list
    ]
    if bool(edge and conn_logic) == True:
        return [("dna45", "dna29")]
    else:
        return []


def dna46_dna29(
    model: House,
) -> List[Tuple[E, A]]:
    edge = [
        ((a, b), {})
        for a in node_ids_2
        if a in "dna46"
        for b in node_ids_2
        if b in "dna29"
    ]
    conn_logic = [
        (conn.a_id, conn.b_id)
        for conn in test_model.room_connections
        if conn.a_id in kit_list and conn.b_id in semi_out_list
    ] + [
        (conn.a_id, conn.b_id)
        for conn in test_model.room_connections
        if conn.a_id in semi_out_list and conn.b_id in kit_list
    ]
    if bool(edge and conn_logic) == True:
        return [("dna46", "dna29")]
    else:
        return []


def dna47_dna29(
    model: House,
) -> List[Tuple[E, A]]:
    edge = [
        ((a, b), {})
        for a in node_ids_2
        if a in "dna47"
        for b in node_ids_2
        if b in "dna29"
    ]
    conn_logic = [
        (conn.a_id, conn.b_id)
        for conn in test_model.room_connections
        if conn.a_id in dining_list and conn.b_id in semi_out_list
    ] + [
        (conn.a_id, conn.b_id)
        for conn in test_model.room_connections
        if conn.a_id in semi_out_list and conn.b_id in dining_list
    ]
    if bool(edge and conn_logic) == True:
        return [("dna47", "dna29")]
    else:
        return []


def edge_name_4_1(
    model: House,
) -> List[Tuple[N, A]]:
    node_ids: List[N] = list(
        chain(
            dna42_dna61(test_model),
            dna42_dna64(test_model),
            # dna42_dna67(test_model),
            # dna42_dna68(test_model),
            # dna43_dna61(test_model),
            # dna43_dna64(test_model),
            # dna43_dna67(test_model),
            # dna43_dna68(test_model),
            # dna46_dna61(test_model),
            # dna46_dna64(test_model),
            # dna46_dna67(test_model),
            # dna46_dna68(test_model),
            # dna46_dna69(test_model),
            # dna47_dna61(test_model),
            # dna47_dna64(test_model),
            # dna47_dna67(test_model),
            # dna47_dna68(test_model),
            # dna47_dna69(test_model),
            # dna48_dna61(test_model),
            # dna48_dna64(test_model),
            # dna48_dna67(test_model),
            # dna48_dna68(test_model),
            # dna48_dna69(test_model),
            # dna49_dna64(test_model),
            # dna49_dna69(test_model),
            # dna51_dna61(test_model),
            # dna51_dna64(test_model),
            # dna51_dna69(test_model),
        )
    )
    return node_ids


# TODO: edge_name_4_1
def dna42_dna61(
    model: House,
) -> List[Tuple[E, A]]:
    edge = [
        ((a, b), {})
        for a in node_ids_2
        if a in "dna42"
        for b in node_ids_2
        if b in "dna61"
    ]

    all_room_list = [room.element_id for room in model.rooms]
    win_count_dict = room_outmost_win_count(model)
    two_sides_room_list = [room for room in all_room_list if win_count_dict[room] >= 2]
    conn_logic = bool(ent_list for ent_list in two_sides_room_list)

    if bool(edge and conn_logic) == True:
        return [("dna42", "dna61")]
    else:
        []


def dna42_dna64(
    model: House,
) -> List[Tuple[E, A]]:
    edge = [
        ((a, b), {})
        for a in node_ids_2
        if a in "dna42"
        for b in node_ids_2
        if b in "dna64"
    ]
    outmost_list = [g.element_id for g in model.glazings if g.outmost]
    outmost_room = [
        room.room_id
        for room in model.room_glazing_relations
        if room.glazing_id in outmost_list
    ]
    conn_logic = bool(ent_list for ent_list in outmost_room)
    if bool(edge and conn_logic) == True:
        return [("dna42", "dna64")]
    else:
        return []


# TODO: 여기서부터 다시 시작


def dna42_dna67(
    model: House,
) -> List[Tuple[E, A]]:
    edge = [
        ((a, b), {})
        for a in node_ids_2
        if a in "dna42"
        for b in node_ids_2
        if b in "dna67"
    ]
    outmost_list = [g.element_id for g in test_model.glazings if g.outmost]
    outmost_room = [
        room.room_id
        for room in test_model.room_glazing_relations
        if room.glazing_id in outmost_list
    ]
    conn_logic = [rel for rel in outmost_room if rel in ent_list]

    if bool(edge and conn_logic) == True:
        return [("dna42", "dna67")]
    else:
        return []


# print(gray_edges_list(test_model))
# print(edge_name_1_1(test_model))
# print(edge_name_1_2(test_model))
# print(edge_name_6(test_model))
# print(dna42_dna64(test_model))


conn_types_open = [RevitObject.ROOM_SEPARATION_LINE]
not_open_glazing = [
    rel.element_id for rel in test_model.glazings if not rel.type_ in conn_types_open
]


south = [
    (rel.room_id)
    for rel in test_model.room_glazing_relations
    if rel.room_id in main_list
    and any((facing in sun_directions) for facing in rel.facings)
]
north = [
    (rel.room_id)
    for rel in test_model.room_glazing_relations
    if rel.room_id in indoor_ancill_list
    and any((facing in opposite_directions) for facing in rel.facings)
]

conn_logic = [
    (rel.room_id)
    for rel in test_model.room_glazing_relations
    if rel.room_id in ent_list
    and any((facing in sun_directions) for facing in rel.facings)
]
glazing_info = [
    (rel.room_id, rel.glazing_id)
    for rel in test_model.room_glazing_relations
    if rel.room_id in ent_list and rel.glazing_id in not_open_glazing
]
outmost_list = [g.element_id for g in test_model.glazings if g.outmost]


# print(south)
# print(north)
# print(conn_logic)
# print(not_open_glazing)
# print(glazing_info)
# print(dna61_windows_on_two_sides(test_model.room_glazing_relations, outmost_list))
# print(multiple_sides())
