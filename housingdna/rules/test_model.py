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


import housingdna.file as hdna

sample_model = hdna.get_model(
    "housingdna/models/Korea_01_위례자연앤셑트럴자이_98.79(완성).json"
)

# test_model = hdna.get_model(
#     "housingdna/models/Japan_01_Sato Kogyo Co._81.58(수정).json"
# )
# test_model = hdna.get_model(
#     "housingdna/models/China_01_2013_119.37(완성)_test2.json"
# )
