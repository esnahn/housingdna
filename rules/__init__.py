# https://github.com/scikit-learn/scikit-learn/blob/main/sklearn/neighbors/__init__.py

# from ._module import function1, function2

from ..model import *

from dataclasses import dataclass


@dataclass
class HousingDNA:
    dna1_is_house: bool


def get_housing_dna(model: House):
    dna = HousingDNA(
        dna1_is_house=True,
    )
    return dna
