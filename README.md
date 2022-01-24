## install

install pyRevit (tested on 4.8.8)
https://github.com/eirannejad/pyRevit/releases

run from PowerShell:
```powershell
Set-ExecutionPolicy RemoteSigned -scope CurrentUser
iwr -useb get.scoop.sh | iex
scoop install aria2
scoop install python@3.8.5 git
pip install --upgrade pip
pip install -r requirements.txt
Add-Content "$env:APPDATA\pyRevit-Master\bin\engines\CPY385\python38._pth" "`n$env:USERPROFILE\scoop\apps\python\3.8.5\Lib\site-packages" -Encoding "UTF8"
```


## usage

- extension: entrypoint for pyrevit extension

    ```python
    from housingdna.extension as get_revit_info, get_model
    revitinfo = get_revit_info(__revit__)
    model = get_model(revitinfo)
    ```

- file: entrypoint for analsys from saved json

    ```python
    from housingdna.file as get_model
    model = get_model(path)
    ```

- cli: entrypoint for pyrevit cli
- model: the data model of a house
- revitapi: extract data from Revit
- mock: save a mock model