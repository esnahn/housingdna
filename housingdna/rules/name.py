from typing import List
from ..model import House, Room
from .type import N


def dnas_room_name(
    model: House,
) -> List[N]:

    semi_out_list = [room.element_id for room in model.rooms if is_semi_outdoor(room)]
    ent_list = [room.element_id for room in model.rooms if is_entrance(room)]
    # living_list = [room.element_id for room in model.rooms if is_living(room)]
    dining_list = [room.element_id for room in model.rooms if is_dining(room)]
    kit_list = [room.element_id for room in model.rooms if is_kitchen(room)]
    bath_list = [room.element_id for room in model.rooms if is_bathroom(room)]
    sto_list = [room.element_id for room in model.rooms if is_storage(room)]
    dress_list = [room.element_id for room in model.rooms if is_dressroom(room)]

    dna: List[N] = []
    for key, eval in [
        ("dna29", semi_out_list),
        ("dna33", dna33_main_entrance(ent_list)),
        ("dna34", dna34_ent_transition(ent_list)),
        ("dna42", ent_list),
        ("dna48", kit_list),
        ("dna49", dining_list),
        ("dna50", bath_list),
        ("dna51", sto_list),
        ("dna53", dress_list),
    ]:
        if bool(eval) == True:
            dna.append(key)
    return dna


def judge_by_name(
    name: str,
    exact_list: List[str] = [],
    partial_list: List[str] = [],
    exclude_exact: List[str] = [],
    exclude_partial: List[str] = [],
) -> bool:
    name = name.rstrip("1234567890")  # remove room number
    name = name.strip(r" .,;'`-=&()[]{}")  # remove spaces and other punctuations

    # use a casefolded copy of the string.
    # The casefolding algorithm is described in section 3.13 of the Unicode Standard.
    name = name.casefold()
    exact_list = [n.casefold() for n in exact_list]
    partial_list = [n.casefold() for n in partial_list]
    exclude_exact = [n.casefold() for n in exclude_exact]
    exclude_partial = [n.casefold() for n in exclude_partial]

    if name in exclude_exact:
        return False
    elif any((part in name) for part in exclude_partial):
        return False
    elif name in exact_list:
        return True
    elif any((part in name) for part in partial_list):
        return True
    else:
        return False


def is_entrance(room: Room) -> bool:
    exact_list = ["???", "ent", "hall", "foyer", "porch"]
    partial_list = ["??????", "??????", "entrance", "entry", "vestibule"]
    return judge_by_name(room.name, exact_list, partial_list)


def is_bedroom(room: Room) -> bool:
    # includes main bedroom (bed at couple's realm)
    exact_list = ["???", "??????", "?????????", "br", "mbr", "bed"]
    partial_list = ["??????", "bedroom"]
    exclude_partial = ["??????"]
    return judge_by_name(
        room.name, exact_list, partial_list, [], exclude_partial=exclude_partial
    )


def is_public(room: Room) -> bool:
    return (
        is_living(room)
        or is_dining(room)
        or is_kitchen(room)
        or is_courtyard(room)
        or is_corridor(room)
    )


def is_living(room: Room) -> bool:
    exact_list = ["L", "LD", "LK", "LDK", "front room"]
    partial_list = [
        "??????",
        "??????",
        "??????",
        "living",
        "sitting",
        "lounge",
        "parlor",
        "parlour",
        "drawing",
        "reception",
        "salon",
        "family",
    ]
    return judge_by_name(room.name, exact_list, partial_list)


def is_dining(room: Room) -> bool:
    exact_list = ["D", "LD", "DK", "LDK"]
    partial_list = [
        "??????",
        "??????",  # ?
        "dining",
        "dine",
        "breakfast",
        "eating",
        "dine",
        "dine",
    ]
    return judge_by_name(room.name, exact_list, partial_list)


def is_kitchen(room: Room) -> bool:
    exact_list = ["K", "LK", "DK", "LDK"]
    partial_list = [
        "??????",
        "??????",
        "kitchen",
        "cook",
        "scullery",
    ]
    return judge_by_name(room.name, exact_list, partial_list)


def is_courtyard(room: Room) -> bool:
    # TODO: expand names
    exact_list = ["??????"]
    partial_list = ["court"]
    return judge_by_name(room.name, exact_list, partial_list)


def is_corridor(room: Room) -> bool:
    exact_list = ["co", "corr", "bdg"]
    partial_list = [
        "??????",
        "??????",
        "??????",
        "?????????",
        "?????????",
        "corridor",
        "hallway",
        "passage",
        "bridge",
    ]
    return judge_by_name(room.name, exact_list, partial_list)


def is_ancillary(room: Room) -> bool:
    return (
        is_bathroom(room)
        or is_dressroom(room)
        or is_storage(room)
        or is_entrance(room)
        or is_semi_outdoor(room)
    )


def is_main(room: Room) -> bool:
    return not is_ancillary(room)


def is_bathroom(room: Room) -> bool:
    exact_list = ["bth", "wc"]
    partial_list = ["?????????", "??????", "?????????", "bath", "toilet", "wash", "powder"]
    return judge_by_name(room.name, exact_list, partial_list)


def is_dressroom(room: Room) -> bool:
    exact_list = ["wic", "closet", "clo"]
    partial_list = [
        "?????????",
        "??????",
        "??????",
        "dress",
        "walk-in closet",
        "w.i.c",
        "w. i. c",
        "shoe",
        "cloak",
    ]
    return judge_by_name(room.name, exact_list, partial_list)


def is_storage(room: Room) -> bool:
    exact_list = ["??????", "sto", "wh", "ldy"]
    partial_list = [
        "??????",
        "??????",
        "?????????",
        "?????????",
        "??????",
        "??????",
        "??????",
        "warehouse",
        "storage",
        "utility",
        "pantry",
        "laundry",
        "linen",
    ]
    return judge_by_name(room.name, exact_list, partial_list)


def is_semi_outdoor(room: Room) -> bool:
    partial_list = [
        "?????????",
        "?????????",
        "?????????",
        "??????",
        "??????",
        "balcony",
        "veranda",
        "terrace",
        "patio",
        "deck",
        "porch",
        "sunroom",
        "sun room",
    ]
    return judge_by_name(room.name, partial_list=partial_list)


def dna33_main_entrance(ent_list: List[int]) -> List[int]:
    # TODO: better handling for houses with no entrance room
    return ent_list


def dna34_ent_transition(ent_list: List[int]) -> List[int]:
    # if there is an entrance, transition is happening.
    return ent_list
