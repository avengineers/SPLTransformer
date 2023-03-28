import json
from pathlib import Path

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

    # Write the dictionary to a JSON file
    tmp_json_file = tmp_path / "data.json"
    with open(tmp_json_file, "w") as f:
        json.dump(data, f)

    assert TransformerConfig(
        input_dir=Path("C:/my/in_dir"),
        output_dir=Path("C:/my/out_dir"),
        variant=Variant("MY", "VAR"),
        source_dir_rel="someRelativeSourceDirectory",
    ) == TransformerConfig.from_json_file(tmp_json_file)


def test_subdir_replacements(tmp_path: Path):
    data = {
        "input_dir": "C:/my/in_dir",
        "output_dir": "C:/my/out_dir",
        "variant": "MY/VAR",
        "subdir_replacements": [
            {"subdir_rel": "COMMON", "replacement": "$ENV{COMMON_BAV2211P01_V2P5P3P1}"}
        ],
    }

    # Write the dictionary to a JSON file
    tmp_json_file = tmp_path / "data.json"
    with open(tmp_json_file, "w") as f:
        json.dump(data, f)

    assert TransformerConfig(
        input_dir=Path("C:/my/in_dir"),
        output_dir=Path("C:/my/out_dir"),
        variant=Variant("MY", "VAR"),
        subdir_replacements=[
            SubdirReplacement("COMMON", "$ENV{COMMON_BAV2211P01_V2P5P3P1}")
        ],
    ) == TransformerConfig.from_json_file(tmp_json_file)
