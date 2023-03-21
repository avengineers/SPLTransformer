import json
from pathlib import Path

from transformer import TransformerConfig


def test_read_config(tmp_path: Path):
    # Create a sample dictionary
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
        variant="MY/VAR",
    ) == TransformerConfig.from_json_file(tmp_json_file)


def test_read_full_config(tmp_path: Path):
    # Create a sample dictionary
    data = {
        "input_dir": "C:/my/in_dir",
        "output_dir": "C:/my/out_dir",
        "variant": "MY/VAR",
        "source_dir_rel": "SRC_LIST",
    }

    # Write the dictionary to a JSON file
    tmp_json_file = tmp_path / "data.json"
    with open(tmp_json_file, "w") as f:
        json.dump(data, f)

    assert TransformerConfig(
        input_dir=Path("C:/my/in_dir"),
        output_dir=Path("C:/my/out_dir"),
        variant="MY/VAR",
        source_dir_rel="SRC_LIST",
    ) == TransformerConfig.from_json_file(tmp_json_file)
