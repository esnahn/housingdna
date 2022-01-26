from typing import List, Optional, Tuple


from ..model import House
from .type import N
from .name import is_ancillary, is_bedroom, is_entrance, is_corridor, is_public
from .attribute import is_mbr
import networkx as nx


def dnas_room_network(
    model: House,
) -> List[N]:
    # room network
    G: nx.Graph = nx.Graph()
    G.add_nodes_from(room.element_id for room in model.rooms)
    G.add_edges_from((conn.a_id, conn.b_id) for conn in model.room_connections)

    rooms = [room.element_id for room in model.rooms]
    pub_list = [room.element_id for room in model.rooms if is_public(room)]
    bed_list = [room.element_id for room in model.rooms if is_bedroom(room)]
    mbr_list = [room.element_id for room in model.rooms if is_mbr(room)]
    ancill_list = [room.element_id for room in model.rooms if is_ancillary(room)]
    ent_list = [room.element_id for room in model.rooms if is_entrance(room)]
    corr_list = [room.element_id for room in model.rooms if is_corridor(room)]

    dna: List[N] = []
    for key, eval in [
        ("dna36", dna36_pub_priv_gradient(G, pub_list, bed_list, ent_list)),
        ("dna38", dna38_direct_connection(G, corr_list)),
        ("dna41", dna41_central_public(G, rooms, pub_list)),
        ("dna45", dna45_couples_realm(G, mbr_list, ancill_list)),
        ("dna46", dna46_childrens_realm(G, bed_list, mbr_list, ancill_list)),
    ]:
        if bool(eval) == True:
            dna.append(key)

    # opposite dna
    for a, not_a in [
        ("dna38", "dna38-1"),
        ("dna41", "dna41-1"),
    ]:
        if not a in dna:
            dna.append(not_a)
    return dna


def dna36_pub_priv_gradient(
    G: nx.Graph, pub_list: List[int], bed_list: List[int], ent_list: List[int]
) -> Optional[List[int]]:
    # TODO: support for gray edges

    try:
        # TODO: better handling for houses with multiple entrances
        ent_room = ent_list[0]
    except:
        # TODO: better handling for houses with no entrance room???
        return None

    pub_PDs: List[int] = [nx.shortest_path_length(G, ent_room, room) for room in pub_list]  # type: ignore
    bed_PDs: List[int] = [nx.shortest_path_length(G, ent_room, room) for room in bed_list]  # type: ignore

    if min(pub_PDs) < max(bed_PDs):
        return pub_list + bed_list
    else:
        return []


def dna38_direct_connection(G_orig: nx.Graph, corr_list: List[int]) -> bool:
    G: nx.Graph = G_orig.copy()
    G.remove_nodes_from(corr_list)

    n_components: int = nx.number_connected_components(G)
    return True if n_components == 1 else False


def dna41_central_public(
    G: nx.Graph, rooms: List[int], pub_list: List[int]
) -> List[int]:
    pub_clo: List[Tuple[int, float]] = [  # type: ignore
        (room, nx.closeness_centrality(G, room)) for room in pub_list
    ]
    max_other_clo: float = max(
        [
            nx.closeness_centrality(G, room) for room in rooms if room not in pub_list
        ]  # type: ignore
    )
    return [room for room, clo in pub_clo if clo > max_other_clo]


def dna45_couples_realm(
    G: nx.Graph,
    mbr_list: List[int],
    ancill_list: List[int],
) -> List[int]:
    # TODO: should include ancillary rooms that "connected"
    # to the? one and only??? main bedroom.
    return mbr_list


def dna46_childrens_realm(
    G: nx.Graph,
    bed_list: List[int],
    mbr_list: List[int],
    ancill_list: List[int],
) -> List[int]:
    # TODO: should include ancillary rooms that "connected"
    # to children's bedrooms.
    return list(set(bed_list) - set(mbr_list))
