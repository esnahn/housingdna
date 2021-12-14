from .model import House


def get_model(path):
    return House.from_json(path)
