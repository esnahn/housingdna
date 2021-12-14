from typing import Union
from housingdna.model import House
from .revitapi import get_project_path
from .revitapi import get_model
from pathlib import Path, PurePath


def save_json(
    model: House,
    filename: Union[str, Path, PurePath],
    save_dir="models/",
):
    path = PurePath(__file__).parent / save_dir / filename
    model.to_json(path)
