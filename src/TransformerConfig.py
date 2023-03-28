from dataclasses import dataclass, field
import json
from typing import Dict, List
import dacite
from pathlib import Path
from SubdirReplacement import SubdirReplacement
from Variant import Variant


@dataclass
class TransformerConfig:
    input_dir: Path
    output_dir: Path
    variant: Variant
    source_dir_rel: str = "Impl/Src"
    build_dir_rel: str = "Impl/Bld"
    third_party_libs_dir_rel: str = "ThirdParty"
    includes_var: str = "CPPFLAGS_INC_LIST"
    sources_var: str = "VC_SRC_LIST"
    subdir_replacements: List[SubdirReplacement] = field(default_factory=list)

    @classmethod
    def from_json_file(cls, file: Path):
        json_data = cls.read_json(file)
        return dacite.from_dict(
            data_class=cls,
            data=json_data,
            config=dacite.Config(
                type_hooks={
                    Path: lambda data: Path(data) if data else None,
                    Variant: lambda data: Variant.from_str(data) if data else None,
                }
            ),
        )

    @staticmethod
    def read_json(config_json_file: Path) -> Dict:
        if config_json_file is None:
            return {}
        with open(config_json_file, "r") as f:
            data = json.load(f)
        return data
