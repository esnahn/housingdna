if __name__ == "__main__" and __package__ is None:
    # set relative import path
    import sys, pathlib

    dir_level = 1

    assert dir_level >= 1
    file_path = pathlib.PurePath(__file__)
    sys.path.append(str(file_path.parents[dir_level]))

    package_path = ""
    for level in range(dir_level - 1, 0 - 1, -1):
        package_path += file_path.parents[level].name
        if level > 0:
            package_path += "."
    __package__ = package_path

from pathlib import Path, PurePath
from typing import List, Tuple, Union

from .file import get_model
from .rules import analyze_housing_dna
from .rules.type import N, E, A


def main():
    mod_path = Path(__file__).parent
    default_path = mod_path / "models"

    # TODO: whether to ask for alternate path for running analysis?
    models_path = default_path
    if not models_path.exists():
        raise FileNotFoundError(f"no directory named {models_path}")

    for json_path in models_path.glob("*.json"):
        print(json_path.stem)
        model = get_model(json_path)
        if not model:
            continue
        nodes, edges = analyze_housing_dna(model)
        # print(nodes)
        # print(edges)
        to_txt_pair(nodes, edges, json_path)


def to_txt_pair(
    nodes: List[Tuple[N, A]],
    edges: List[Tuple[E, A]],
    path: Union[str, Path, PurePath],
) -> None:
    if not isinstance(path, Path):
        path = Path(path)
    if not path.parent.exists():
        path.parent.mkdir(parents=True)

    # nodes
    try:
        with open(
            str(path.with_name(path.stem + "_nodes.txt")), "w", encoding="utf-8"
        ) as file:
            file.writelines([to_node_line(node) + "\n" for node in nodes])
    except Exception as e:
        raise Exception(f"fail to save nodes of {path}", e)

    # edges
    try:
        with open(
            str(path.with_name(path.stem + "_edges.txt")), "w", encoding="utf-8"
        ) as file:
            file.writelines([to_edge_line(edge) + "\n" for edge in edges])
    except Exception as e:
        raise Exception(f"fail to save edges of {path}", e)


def to_node_line(node: Tuple[N, A]) -> str:
    # "ID" "name"
    return f'"{node[0]}" "{node[1]["name"]}"'


def to_edge_line(edge: Tuple[E, A]) -> str:
    # "ID_from" "ID_to"
    return f'"{edge[0][0]}" "{edge[0][1]}"'


if __name__ == "__main__":
    main()
