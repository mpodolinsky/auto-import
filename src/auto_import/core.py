from __future__ import annotations

import importlib
import shutil
import subprocess
import sys

# Import name -> PyPI name, where they differ.
KNOWN_MAPPINGS = {
    "cv2": "opencv-python",
    "PIL": "pillow",
    "sklearn": "scikit-learn",
    "skimage": "scikit-image",
    "yaml": "pyyaml",
    "bs4": "beautifulsoup4",
    "dateutil": "python-dateutil",
    "dotenv": "python-dotenv",
    "attr": "attrs",
    "Crypto": "pycryptodome",
    "serial": "pyserial",
    "OpenSSL": "pyopenssl",
    "jwt": "pyjwt",
    "docx": "python-docx",
    "pptx": "python-pptx",
    "fitz": "pymupdf",
    "git": "gitpython",
    "magic": "python-magic",
    "umap": "umap-learn",
    "google.protobuf": "protobuf",
    "mpl_toolkits": "matplotlib",
}


def module_to_package(module: str) -> str:
    """Map an import name (possibly dotted) to the PyPI distribution to install."""
    if module in KNOWN_MAPPINGS:
        return KNOWN_MAPPINGS[module]
    top = module.split(".")[0]
    return KNOWN_MAPPINGS.get(top, top)


class AutoImporter:
    def __init__(self, ip, max_installs: int = 10, confirm: bool = False, verbose: bool = True):
        self.ip = ip
        self.max_installs = max_installs
        self.confirm = confirm
        self.verbose = verbose
        self.failed: set[str] = set()
        self._cell: str | None = None
        self._depth = 0
        self._installs = 0

    # -- lifecycle -------------------------------------------------------
    def register(self):
        self.ip.events.register("pre_run_cell", self._pre_run_cell)
        self.ip.set_custom_exc((ModuleNotFoundError,), self._handle)

    def unregister(self):
        self.ip.events.unregister("pre_run_cell", self._pre_run_cell)
        # Restore default handling for ModuleNotFoundError.
        self.ip.CustomTB = None
        self.ip.custom_exceptions = ()

    def _pre_run_cell(self, info):
        if self._depth == 0:
            self._cell = info.raw_cell
            self._installs = 0

    # -- installing ------------------------------------------------------
    def install(self, package: str) -> bool:
        if shutil.which("uv") and not _has_pip():
            cmd = ["uv", "pip", "install", "--python", sys.executable, package]
        else:
            cmd = [sys.executable, "-m", "pip", "install", package]
        self._log(f"[auto_import] installing '{package}' ...")
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            self._log(f"[auto_import] failed to install '{package}':\n{proc.stderr.strip()[-1500:]}")
            return False
        importlib.invalidate_caches()
        self._log(f"[auto_import] installed '{package}'")
        return True

    # -- exception hook --------------------------------------------------
    def _handle(self, shell, etype, evalue, tb, tb_offset=None):
        name = getattr(evalue, "name", None)
        package = module_to_package(name) if name else None
        can_retry = (
            package
            and package not in self.failed
            and self._cell is not None
            and self._depth < self.max_installs
            and self._installs < self.max_installs
        )
        if can_retry and self.confirm:
            can_retry = input(f"Install '{package}'? [y/N] ").strip().lower() in ("y", "yes")
        if not can_retry or not self.install(package):
            if package:
                self.failed.add(package)
            shell.showtraceback((etype, evalue, tb), tb_offset=tb_offset)
            return None
        self._installs += 1
        self._depth += 1
        try:
            self._log("[auto_import] re-running cell")
            shell.run_cell(self._cell, store_history=False)
        finally:
            self._depth -= 1
        return None

    def _log(self, msg: str):
        if self.verbose:
            print(msg, file=sys.stderr)


def _has_pip() -> bool:
    return importlib.util.find_spec("pip") is not None


_instance: AutoImporter | None = None


def load_ipython_extension(ip):
    global _instance
    if _instance is None:
        _instance = AutoImporter(ip)
        _instance.register()


def unload_ipython_extension(ip):
    global _instance
    if _instance is not None:
        _instance.unregister()
        _instance = None
