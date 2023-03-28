import textwrap
import pytest
from pathlib import Path

from transformer import LegacyPartsCMakeGenerator


@pytest.fixture
def generator():
    sources = [Path("path/to/source1.c"), Path("path/to/source2.c")]
    generator = LegacyPartsCMakeGenerator(sources)
    return generator


def test_to_file(generator, tmp_path):
    file_path = tmp_path / "parts.cmake"
    generator.to_file(file_path)
    assert file_path.exists()
    with open(file_path, "r") as f:
        assert f.read() == generator.to_string()


def test_to_string(generator: LegacyPartsCMakeGenerator):
    expected_output = textwrap.dedent(
        """\
        # Generated by Transformer
        spl_add_source(path/to/source1.c)
        spl_add_source(path/to/source2.c)
        """
    )
    assert generator.to_string() == expected_output