import textwrap
import pytest
from pathlib import Path

from transformer import LegacyCMakeListsGenerator


def test_to_string():
    generator = LegacyCMakeListsGenerator()
    expected_output = textwrap.dedent(
        """\
        # Generated by Transformer
        include(${VARIANT}/parts.cmake)
        spl_create_component()
        """
    )
    assert generator.to_string() == expected_output