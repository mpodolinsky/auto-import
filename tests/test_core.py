import sys
from IPython.core.interactiveshell import InteractiveShell

from auto_import import AutoImporter, module_to_package


def test_mapping():
    assert module_to_package("cv2") == "opencv-python"
    assert module_to_package("yaml.foo") == "pyyaml"
    assert module_to_package("requests") == "requests"


def test_installs_and_reruns(tmp_path, monkeypatch):
    ip = InteractiveShell.instance()
    imp = AutoImporter(ip, verbose=False)
    imp.register()
    calls = []

    def fake_install(pkg):
        calls.append(pkg)
        (tmp_path / "fake_missing_mod.py").write_text("VALUE = 42\n")
        monkeypatch.syspath_prepend(str(tmp_path))
        import importlib; importlib.invalidate_caches()
        return True

    imp.install = fake_install
    try:
        ip.run_cell("import fake_missing_mod\nresult = fake_missing_mod.VALUE")
        assert calls == ["fake_missing_mod"]
        assert ip.user_ns["result"] == 42
    finally:
        imp.unregister()
        sys.modules.pop("fake_missing_mod", None)


def test_failed_install_shows_error():
    ip = InteractiveShell.instance()
    imp = AutoImporter(ip, verbose=False)
    imp.register()
    imp.install = lambda pkg: False
    try:
        r = ip.run_cell("import definitely_not_a_real_mod_xyz")
        assert r.error_in_exec is not None or r.error_before_exec is not None
        assert "definitely_not_a_real_mod_xyz" in imp.failed
    finally:
        imp.unregister()
