import pytest

from syllabot.fixtures import fixture_dir, load_courses
from syllabot.store import Store


@pytest.fixture
def fixtures():
    return fixture_dir()


@pytest.fixture
def store(tmp_path, fixtures):
    s = Store(tmp_path / "state")
    s.init(courses=load_courses(fixtures))
    return s
