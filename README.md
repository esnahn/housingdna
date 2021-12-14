- extension: entrypoint for pyrevit extension

    ```python
    import housingdna.extension as hdna
    model = hdna.get_model(uiapp)
    ```

- file: entrypoint for analsys from saved json

    ```python
    import housingdna.file as hdna
    model = hdna.get_model(path)
    ```

- cli: entrypoint for pyrevit cli
- model: the data model of a house
- revitapi: populate and return the model
- mock: save a mock model to `mock.json`