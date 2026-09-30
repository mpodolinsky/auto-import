# auto-import

IPython/Jupyter extension: when a cell raises `ModuleNotFoundError`, it installs the
missing package into the current kernel's environment (`pip`, or `uv pip` in pip-less
venvs) and re-runs the cell automatically.

```python
%pip install auto-import   # or: pip install -e .
%load_ext auto_import
```

Then `import pandas` (or `cv2`, `sklearn`, ...) just works. Import names that differ
from PyPI names are mapped in `KNOWN_MAPPINGS` (`cv2` -> `opencv-python`, etc.).

To load it in every notebook, add to `~/.ipython/profile_default/ipython_config.py`:

```python
c.InteractiveShellApp.extensions = ["auto_import"]
```

## Caveats
- The whole cell is re-run, so side effects before the failing import repeat.
- Installing packages by import name can pull a wrong/typosquatted package. For safety,
  set `AutoImporter(ip, confirm=True)` to be prompted first.
- Only `ModuleNotFoundError` is handled; version conflicts and `ImportError` are not.
