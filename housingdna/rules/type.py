from typing import Dict, Tuple, Union


N = Union[str, int, Tuple[Union[str, int], ...]]  # networkx node type
E = Tuple[N, N]  # networkx edge args (in tuple) type
A = Dict[str, Union[str, int, float]]  # networkx attributes kwargs (in dict) type
