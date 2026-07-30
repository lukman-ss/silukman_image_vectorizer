import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--run-stress", action="store_true", default=False, help="run stress tests"
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "stress: mark test as a stress test (large images)")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-stress"):
        return
    skip_stress = pytest.mark.skip(reason="need --run-stress option to run")
    for item in items:
        if "stress" in item.keywords:
            item.add_marker(skip_stress)
