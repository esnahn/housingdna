- extension: entrypoint for pyrevit extension

    ```python
    import housingdna.extension as hdna
    model = hdna.get_model(uiapp)
    ```

- mock: return a mock model

    ```python
    import housingdna.mock as hdna
    model = hdna.get_model(path)
    ```

- cli: entrypoint for pyrevit cli
- model: the data model of a house
- revitapi: populate and return the model
