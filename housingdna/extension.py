if __name__ == "__main__" and __package__ is None:
    # set relative import path
    import sys, pathlib

    dir_level = 1

    assert dir_level >= 1
    package_path = pathlib.PurePath(__file__).parents[dir_level - 1]

    __package__ = package_path.name
    sys.path.append(str(package_path.parent))


from itertools import combinations
import math
from typing import (
    Any,
    Collection,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
)
import numpy as np
from pathlib import Path, PurePath
from shapely.geometry import Point, LineString, Polygon
from shapely.geometry.geo import box

from housingdna.model import (
    Direction,
    House,
    Length,
    Glazing,
    RevitInfo,
    RevitObject,
    Room,
    RoomConnection,
    RoomGlazingRelation,
)

if __name__ != "__main__":
    from housingdna.revitapi import get_revit_info  # type:ignore


def save_json(
    model: House,
    filename: Union[str, Path, PurePath],
    save_dir: Union[str, Path, PurePath] = "models/",
) -> None:
    path = PurePath(__file__).parent / save_dir / filename
    model.to_json(path)


def to_polygon(rings: Sequence[Sequence[Tuple[float, float]]]) -> Polygon:
    return Polygon(rings[0], rings[1:])


def to_segmented_lines(
    polyline: Sequence[Tuple[float, float]], true_north: float = 0
) -> Optional[List[Tuple[Direction, LineString]]]:
    if len(polyline) <= 1:
        return None

    # assuming number of points >= 2, last index >= 1
    first_i = 0  # set to the first point
    # calculate bearing of the advance
    bearing = (
        azimuth(polyline[0], polyline[1])  # between first two points
        - true_north  # make the true north == 0
    )
    # into 8-direction
    last_direction = to_direction(bearing)
    if len(polyline) == 2:
        # return the whole line
        return [(last_direction, LineString(polyline))]

    # assuming number of points >= 3, last index >= 2
    lines: List[Tuple[Direction, LineString]] = []
    for i in range(2, len(polyline)):
        # calculate bearing of the advance
        bearing = (
            azimuth(polyline[i - 1], polyline[i])  # between (currently) last two points
            - true_north  # make the true north == 0
        )
        # into 8-direction
        direction = to_direction(bearing)
        if direction != last_direction:
            # create a linestring excluding this point
            lines.append((last_direction, LineString(polyline[first_i:i])))
            # last point will be shared between two linestrings
            first_i = i - 1
            # this bearing for next linestring
            last_direction = direction
    # for the last linestring
    lines.append((last_direction, LineString(polyline[first_i:])))
    return lines


def azimuth(point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
    """azimuth between 2 shapely points in radian 0 to 2pi.

    https://gis.stackexchange.com/questions/200971/angle-at-intersection-point-from-two-lines

    >>> azimuth((0, 0), (0, 1))  # north == 0
    0.0
    >>> azimuth((0, 0), (1, 0))  # east == 1/2*pi  # doctest: +ELLIPSIS
    1.57...
    >>> azimuth((0, 0), (0, -1))  # south == pi  # doctest: +ELLIPSIS
    3.14...
    >>> azimuth((0, 0), (-1, 0))  # west == 3/2*pi  # doctest: +ELLIPSIS
    4.71...
    """
    x1, y1 = point1
    x2, y2 = point2

    angle: float = np.arctan2(x2 - x1, y2 - y1)
    return angle if angle >= 0 else angle + 2 * math.pi


def to_direction(bearing: float) -> Direction:
    return Direction(
        round(
            (
                (bearing / (2 * math.pi))  # in rotations (from radian)
                + 1  # add 1 rotation to make it always positive
            )
            * 8  # in 1/8 rotations
        )  # round to closest 1/8 rotations
        % 8  # remove full rotations, which could exist from adding 1 full rotation
        + 1  # make the true north == 1 instead of 0 (rotation)
    )  # convert it to Direction


def center_of_overlap(*polygons: Polygon) -> Optional[Tuple[float, float]]:
    overlap = polygons[0]
    for p in polygons[1:]:
        if overlap:
            overlap: Optional[Polygon] = overlap.intersection(p)  # type: ignore
        else:
            return None
    if overlap:
        c: Point = overlap.centroid  # type: ignore
        if c:
            return float(c.x), float(c.y)  # type: ignore

    return None


def direction_from_sides(direction: Direction) -> Tuple[Direction, Direction]:
    if direction in [Direction.UP, Direction.DOWN]:
        return direction, direction  # same all around
    elif 1 <= direction.value <= 8:
        return (
            # from left:
            Direction((direction.value - 1 + 2) % 8 + 1),  # rotate 2/8 rotation CW
            # from right:
            Direction((direction.value - 1 - 2 + 8) % 8 + 1),  # rotate 2/8 rotation CCW
        )
    else:
        raise Exception(f"can't recognize {type(direction)} {direction}")


def sided_buffers(
    line: LineString,
    depth: float = 1,  # one foot
) -> Tuple[Polygon, Polygon]:
    # buffer area with depth (in feet), flat cap, bevel join
    # a positive distance indicates the left-hand side
    left_buffer: Polygon = line.buffer(  # type: ignore
        abs(depth), cap_style=2, join_style=3, single_sided=True
    )
    # a negative distance indicates the right-hand side
    right_buffer: Polygon = line.buffer(  # type: ignore
        -abs(depth), cap_style=2, join_style=3, single_sided=True
    )
    return left_buffer, right_buffer


def facings_from_poly(
    buffers: Sequence[Tuple[Tuple[Direction, Direction], Tuple[Polygon, Polygon]]],
    polygon: Polygon,
) -> Set[Direction]:
    facings: Set[Direction] = set()
    for (direction_from_left, direction_from_right), (
        left_buffer,
        right_buffer,
    ) in buffers:
        left_area = left_buffer.intersection(polygon).area  # type: ignore
        right_area = right_buffer.intersection(polygon).area  # type: ignore
        if not left_area and not right_area:  # if there is no overlap
            continue  # ignore

        if left_area >= right_area:  # if room is on left side
            facings.add(direction_from_left)
        else:
            facings.add(direction_from_right)
    return facings


def get_model(r: RevitInfo) -> House:
    def _count_value(from_: Mapping[Any, Collection[Any]], key: Any) -> int:
        val = from_.get(key)
        return len(val) if val else 0

    def count_rooms(key: Any) -> int:
        return _count_value(r.rel_rooms, key)

    print("building the very model of a modern, major housing 🏗")
    rooms: Set[Room] = set(
        Room(element_id=id_, name=r.names[id_], height=Length.from_ft(r.heights[id_]))
        for id_ in r.rooms
    )

    room_conns: Set[RoomConnection] = set()
    for id_list, object_type in [
        (r.doors, RevitObject.DOOR),
        (r.separation_lines, RevitObject.ROOM_SEPARATION_LINE),
    ]:
        for glazing_id in id_list:
            if count_rooms(glazing_id) >= 2:
                for pair in combinations(r.rel_rooms[glazing_id], 2):
                    room_conns.add(RoomConnection(*sorted(pair), type_=object_type))

    glazings: set[Glazing] = set()
    glazings.update(
        Glazing(
            element_id=id_,
            type_=object_type,
            outmost=(count_rooms(id_) == 1),
        )
        for id_list, object_type in [
            (r.windows, RevitObject.WINDOW),
            (r.curtain_walls, RevitObject.CURTAIN_WALL),
            (r.separation_lines, RevitObject.ROOM_SEPARATION_LINE),
        ]
        for id_ in id_list
        if count_rooms(id_) >= 1  # sanity check: a glazing should have a room.
    )
    # add transparent doors
    transparent_doors = [
        d
        for d in r.doors
        if (t := r.transparencies.get(d)) and t >= 10  # ranges from 0 to 100
    ]
    glazings.update(
        Glazing(
            element_id=id_,
            type_=object_type,
            outmost=(count_rooms(id_) == 1),
        )
        for id_list, object_type in [
            (transparent_doors, RevitObject.DOOR),
        ]
        for id_ in id_list
        if count_rooms(id_) >= 1  # sanity check: a glazing should have a room.
    )

    room_polygons = {
        room: to_polygon(b) for room in r.rooms if (b := r.boundaries.get(room))
    }
    room_glazing_relations: List[RoomGlazingRelation] = []
    # for point objects
    for glazing_id in transparent_doors + r.windows:
        rel_rooms = r.rel_rooms.get(glazing_id)
        coord = r.points.get(glazing_id)

        if not rel_rooms or not coord:
            continue

        x, y = coord
        g_box: Polygon = box(x - 1, y - 1, x + 1, y + 1)

        for room in rel_rooms:
            room_poly = room_polygons.get(room)
            if room_poly is None:
                continue

            c_overlap = center_of_overlap(g_box, room_poly)
            if c_overlap is None:
                continue

            # calculate bearing from room (overlap) to glazing
            bearing = (
                azimuth(c_overlap, coord) - r.true_north  # make the true north == 0
            )
            # into 8-direction
            direction = to_direction(bearing)

            room_glazing_relations.append(
                RoomGlazingRelation(
                    room_id=room, glazing_id=glazing_id, facings=(direction,)
                )
            )
    # for linear objects
    for glazing_id in r.curtain_walls + r.separation_lines:
        rel_rooms = r.rel_rooms.get(glazing_id)
        points = r.lines.get(glazing_id)
        segs = to_segmented_lines(points, true_north=r.true_north) if points else None

        if not rel_rooms or not segs:
            continue

        buffers = [
            (direction_from_sides(seg[0]), sided_buffers(seg[1])) for seg in segs
        ]

        for room in rel_rooms:
            room_poly = room_polygons.get(room)

            if room_poly is None:
                continue

            if facings := facings_from_poly(buffers, room_poly):
                room_glazing_relations.append(
                    RoomGlazingRelation(
                        room_id=room, glazing_id=glazing_id, facings=tuple(facings)
                    )
                )
    return House(
        rooms=tuple(rooms),
        room_connections=tuple(room_conns),
        glazings=tuple(glazings),
        room_glazing_relations=tuple(room_glazing_relations),
    )


if __name__ == "__main__":
    import doctest

    doctest.testmod()
