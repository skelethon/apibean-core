import os

import pytest

os.environ["ENV"] = "test"

if os.getenv("ENV") not in ["test"]:
    msg = f"ENV is not test, it is {os.getenv('ENV')}"
    pytest.exit(msg)

@pytest.fixture
def data_initializer():
    return {}


@pytest.fixture
def client(data_initializer):
    return {}


@pytest.fixture
def container():
    return {}
