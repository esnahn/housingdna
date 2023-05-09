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
from typing import List, Tuple
from ..model import (House, RevitObject, Direction)
from .type import N, E, A
from .nodes import node_names
from .name import dna34_ent_transition, dna33_main_entrance, dnas_room_name, is_main, is_bedroom, is_kitchen, is_semi_outdoor, is_entrance, is_dining, is_bathroom, is_storage, is_dressroom, is_corridor, is_public, is_ancillary, is_living, is_semi_outdoor
from .attribute import is_mbr, dnas_attribute
from .room_network import dnas_room_network, dna36_pub_priv_gradient, dna38_direct_connection, dna41_central_public, dna44_couples_realm, dna45_childrens_realm
from .glazing_network import dnas_glazing_network, dna37_indoor_for_sunlight, dna52_bedroom_for_sunlight
from housingdna.rules import edges


# 분석 대상 불러오기: revit file 명 ""에 추가할 것
test_model = hdna.get_model(
    "housingdna/models/Japan_01_Sato Kogyo Co._81.58(test).json")


# 네트워크 만들기
G = nx.Graph()
G.add_edges_from((conn.a_id, conn.b_id)
                 for conn in test_model.room_connections)
list(G.edges)

list_edges = [G.edges]
# print(list_edges)

# 공간 분류 리스트 정리
rooms = [room.element_id for room in test_model.rooms]
pub_list = [room.element_id for room in test_model.rooms if is_public(room)]
mbr_list = [room.element_id for room in test_model.rooms if is_mbr(room)]
ancill_list = [
    room.element_id for room in test_model.rooms if is_ancillary(room)]
semi_out_list = [
    room.element_id for room in test_model.rooms if is_semi_outdoor(room)]
ent_list = [room.element_id for room in test_model.rooms if is_entrance(room)]
# living_list = [room.element_id for room in model.rooms if is_living(room)]
dining_list = [room.element_id for room in test_model.rooms if is_dining(room)]
kit_list = [room.element_id for room in test_model.rooms if is_kitchen(room)]
bath_list = [room.element_id for room in test_model.rooms if is_bathroom(room)]
sto_list = [room.element_id for room in test_model.rooms if is_storage(room)]
dress_list = [
    room.element_id for room in test_model.rooms if is_dressroom(room)]
corr_list = [room.element_id for room in test_model.rooms if is_corridor(room)]
bed_list = [room.element_id for room in test_model.rooms if is_bedroom(room)]
living_list = [room.element_id for room in test_model.rooms if is_living(room)]
main_list = [room.element_id for room in test_model.rooms if is_main(room)]


def dnas_complex(
    model: House,
) -> List[N]:

    dna: List[N] = []
    for key, eval in [
        ("dna43", dna43_fun_corr(test_model)), ("dna54",
                                                dna54_Independent_rooms(test_model))
    ]:
        if bool(eval) == True:
            dna.append(key)
    return dna

# 43.지루하지 않는 복도 정의


def dna43_fun_corr(
    model: House,
) -> List[N]:
    # room-glazing network
    conn_types_open = [RevitObject.ROOM_SEPARATION_LINE]
    conn_types_win = [RevitObject.WINDOW, RevitObject.CURTAIN_WALL]
    glazing_types = [(gla.element_id)
                     for gla in test_model.glazings if gla.type_ in conn_types_win]
    # 외기에 면한 창 리스트
    outmost_list = [g.element_id for g in test_model.glazings if g.outmost]
    # 외기에 면한 방 리스트
    outmost_room = [(out.room_id)
                    for out in model.room_glazing_relations if out.room_id in rooms and out.glazing_id in outmost_list]

    # 1. 복도가 없을 때
    fun_corr1 = [room for room in corr_list]
    # 2. 복도가 있을 때, 복도와 연결된 다른 공간이 오픈되어 있는 경우. but 현관과 복도 오픈 연결은 제외
    fun_corr2 = [
        (conn.a_id, conn.type_) for conn in test_model.room_connections if conn.a_id in corr_list and conn.type_ in conn_types_open and not ancill_list] + [
        (conn.b_id, conn.type_) for conn in test_model.room_connections if conn.b_id in corr_list and conn.type_ in conn_types_open and not ancill_list]
    # 3. 복도가 있을 때, 복도에 외기로의 창이 있는 경우. 외기에 면한 창만을 어떻게 설정????
    fun_corr3 = [rel for rel in outmost_room if rel in corr_list]

    # return fun_corr1, fun_corr2, fun_corr3, outmost_room

    if bool(fun_corr1) == False or bool(fun_corr2 or fun_corr3) == True:
        return True


# 39_명암의 대비가 강조되는 공간계획
# TODO: code


# 54_독립된 방
def dna54_Independent_rooms(
    model: House,
) -> List[N]:
    conn_types_door = [RevitObject.DOOR]
    independent_rooms1 = [(conn.a_id, conn.type_)
                          for conn in test_model.room_connections if conn.a_id in bed_list and conn.type_ in conn_types_door]
    independent_rooms2 = [(conn.b_id, conn.type_)
                          for conn in test_model.room_connections if conn.b_id in bed_list and conn.type_ in conn_types_door]

    return set(independent_rooms1) - set(independent_rooms2)


# print(dna54_Independent_rooms(test_model))
