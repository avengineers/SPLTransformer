import json
from pathlib import Path
from typing import Dict

import pytest

from transformer import SubdirReplacement, TransformerConfig, Variant


def test_mandatory_config_json(tmp_path: Path):
    data = {
        "input_dir": "C:/my/in_dir",
        "output_dir": "C:/my/out_dir",
        "variant": "MY/VAR",
    }

    # Write the dictionary to a JSON file
    tmp_json_file = tmp_path / "data.json"
    with open(tmp_json_file, "w") as f:
        json.dump(data, f)

    assert TransformerConfig(
        input_dir=Path("C:/my/in_dir"),
        output_dir=Path("C:/my/out_dir"),
        variant=Variant("MY", "VAR"),
    ) == TransformerConfig.from_json_file(tmp_json_file)


def test_full_optional_config(tmp_path: Path):
    data = {
        "input_dir": "C:/my/in_dir",
        "output_dir": "C:/my/out_dir",
        "variant": "MY/VAR",
        "source_dir_rel": "someRelativeSourceDirectory",
    }
    assert TransformerConfig(
        input_dir=Path("C:/my/in_dir"),
        output_dir=Path("C:/my/out_dir"),
        variant=Variant("MY", "VAR"),
        source_dir_rel="someRelativeSourceDirectory",
    ) == TransformerConfig.from_dict(data)


def test_subdir_replacements(tmp_path: Path):
    data = {
        "input_dir": "C:/my/in_dir",
        "output_dir": "C:/my/out_dir",
        "variant": "MY/VAR",
        "subdir_replacements": [
            {"subdir_rel": "COMMON", "replacement": "$ENV{COMMON_BAV2211P01_V2P5P3P1}"}
        ],
    }
    config = TransformerConfig.from_dict(data)
    assert [
        SubdirReplacement("COMMON", "$ENV{COMMON_BAV2211P01_V2P5P3P1}")
    ] == config.subdir_replacements


def test_variant_linker_file(tmp_path: Path):
    data = {
        "input_dir": "C:/my/in_dir",
        "output_dir": "C:/my/out_dir",
        "variant": "MY/VAR",
        "variant_compiler_flags": "my_variant_c_flags",
        "variant_linker_file": "my/linker.lsl",
        "variant_link_flags": "my_variant_link_flags",
        "cmake_toolchain_file": "my/toolchain.cmake",
    }

    config = TransformerConfig.from_dict(data)
    assert "my_variant_c_flags" == config.variant_compiler_flags
    assert "my/linker.lsl" == config.variant_linker_file
    assert "my_variant_link_flags" == config.variant_link_flags
    assert "my/toolchain.cmake" == config.cmake_toolchain_file
