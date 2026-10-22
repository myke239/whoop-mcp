from pathlib import Path


def pytest_configure(config):
    # Pytest creates basetemp itself but does not create its parent on a fresh checkout.
    (Path(config.rootpath) / "work").mkdir(exist_ok=True)
