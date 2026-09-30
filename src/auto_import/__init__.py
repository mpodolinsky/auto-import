"""Install missing packages automatically in IPython/Jupyter and re-run the cell.

Usage in a notebook::

    %pip install auto-import   # once
    %load_ext auto_import

Optional settings via ``%auto_import`` (see README).
"""
from .core import AutoImporter, load_ipython_extension, unload_ipython_extension, module_to_package

__all__ = ["AutoImporter", "load_ipython_extension", "unload_ipython_extension", "module_to_package"]
