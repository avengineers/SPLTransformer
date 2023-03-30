from dataclasses import dataclass, field
import json
from typing import Any, Dict, List, Optional
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
    variant_compiler_flags: str = "TODO: to be replaced with compiler flags"
    variant_linker_file: str = "TODO: to be replaced with the .lsl file path"
    variant_link_flags: str = "TODO: to be replaced with linker flags"
    cmake_toolchain_file: str = (
        "TODO: to be replaced with the toolchain cmake file path"
    )

    @classmethod
    def from_json_file(cls, file: Path):
        return cls.from_dict(cls.read_json(file))

    @classmethod
    def from_dict(cls, dictionary: Any):
        return dacite.from_dict(
            data_class=cls,
            data=dictionary,
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
