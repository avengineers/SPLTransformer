#!/usr/bin/env python3

"""Transformer

Usage:
  transformer.py (--source=<source directory> --target=<target directory> --variant=<variant> | --config=<config_file>)
  transformer.py (-h | --help)

Options:
  -h --help            Show this screen.
  --source=DIR         Source directory holding a Dimensions make project
  --target=DIR         Target directory for the transformed CMake project
  --variant=VARIANT    VARIANT of the transformed CMake project (e.g., 'customer1_subsystem_flavor')
  --config=FILE        JSON configuration file

"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import glob
import sys
import textwrap
from typing import Dict, List
from docopt import docopt
import logging
import subprocess
import shutil
import os
from pathlib import WindowsPath, Path
import json
from SubdirReplacement import SubdirReplacement
from TransformerConfig import TransformerConfig
from Variant import Variant
from PathSearchAndReplace import PathSearchAndReplace
from LegacyBuildSystem import LegacyBuildSystem


class FileGenerator(ABC):
    def to_file(self, file: Path) -> None:
        file.parent.mkdir(parents=True, exist_ok=True)
        with open(file, "w") as f:
            f.write(self.to_string())

    @abstractmethod
    def to_string(self) -> str:
        """Dump content to string"""


@dataclass
class VariantPartsCMakeGenerator(FileGenerator):
    include_paths: List[Path]
    third_party_libs: List[Path]
    variant: Variant
    subdir_extra_replacements: List[SubdirReplacement] = field(default_factory=list)

    def to_string(self) -> str:
        return "\n".join(
            [
                "# Generated by Transformer",
                self.cmake_includes(),
                "",
                f"spl_add_component(legacy/{self.variant})",
                self.cmake_link_libraries(),
                "",
            ]
        )

    def cmake_includes(self) -> str:
        return "\n".join(
            [f"spl_add_include({self.replace(inc)})" for inc in self.include_paths]
        )

    def replace(self, path: Path) -> str:
        replacer = PathSearchAndReplace(
            self.subdir_extra_replacements
            + [SubdirReplacement("/", "${PROJECT_SOURCE_DIR}/legacy/${VARIANT}/src")]
        )
        return replacer.replace_path(path).as_posix()

    def cmake_link_libraries(self) -> str:
        return "\n".join(
            [
                "target_link_libraries(${LINK_TARGET_NAME} ${CMAKE_CURRENT_LIST_DIR}/Lib/"
                + lib.as_posix()
                + ")"
                for lib in self.third_party_libs
            ]
        )


@dataclass
class LegacyPartsCMakeGenerator(FileGenerator):
    sources: List[Path]

    def to_string(self) -> str:
        return "\n".join(["# Generated by Transformer", self.cmake_sources(), ""])

    def cmake_sources(self) -> str:
        return "\n".join(
            [f"spl_add_source({source.as_posix()})" for source in self.sources]
        )


class LegacyCMakeListsGenerator(FileGenerator):
    def __init__(self) -> None:
        super().__init__()

    def to_string(self) -> str:
        return textwrap.dedent(
            """\
        # Generated by Transformer
        include(${VARIANT}/parts.cmake)
        spl_create_component()
        """
        )


class Transformer:
    def __init__(
        self,
        config: TransformerConfig,
    ):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.name = type(self).__name__
        self.config: TransformerConfig = config

    @property
    def input_dir(self) -> Path:
        return self.config.input_dir

    @property
    def output_dir(self) -> Path:
        return self.config.output_dir

    @property
    def variant(self) -> str:
        return self.config.variant

    @property
    def legacy_dir(self) -> Path:
        return self.output_dir.joinpath(f"legacy")

    @property
    def legacy_variant_dir(self) -> Path:
        return self.legacy_dir.joinpath(f"{self.variant}")

    @property
    def variant_dir(self) -> Path:
        return self.output_dir.joinpath(f"variants/{self.variant}")

    @property
    def make_dump_file(self) -> Path:
        return self.variant_dir / "original_make_vars.txt"

    @property
    def variant_parts_cmake_file(self) -> Path:
        return self.variant_dir / "parts.cmake"

    @property
    def legacy_parts_cmake_file(self) -> Path:
        return self.legacy_variant_dir / "parts.cmake"

    @property
    def legacy_cmake_lists_file(self) -> Path:
        return self.legacy_dir / "CMakeLists.txt"

    def run(self):
        self.create_folder_structure()
        self.create_legacy_make_variables_dump_file()
        self.copy_source_files()
        self.copy_libs()
        self.copy_vscode_files()
        self.create_cmake_project(LegacyBuildSystem(self.make_dump_file, self.config))
        self.copy_linker_definition()
        self.copy_config()
        self.create_variant_json()

    def create_cmake_project(self, legacy_build_system: LegacyBuildSystem) -> None:
        VariantPartsCMakeGenerator(
            legacy_build_system.get_include_paths(),
            legacy_build_system.get_thirdparty_libs(),
            self.variant,
        ).to_file(self.variant_parts_cmake_file)
        LegacyPartsCMakeGenerator(legacy_build_system.get_source_paths()).to_file(
            self.legacy_parts_cmake_file
        )
        LegacyCMakeListsGenerator().to_file(self.legacy_cmake_lists_file)

    def create_folder_structure(self) -> None:
        variant_and_legacy_folders = [self.variant_dir, self.legacy_variant_dir]
        toolchain_folders = [
            "tools/toolchains/gcc",
            "tools/toolchains/comp_201754",
            "tools/toolchains/comp_201914",
            "tools/toolchains/TriCore_v6p2r2p2",
            "tools/toolchains/TriCore_v6p3r1",
        ]

        toolchain_paths = [
            self.config.output_dir.joinpath(folder) for folder in toolchain_folders
        ]

        for folder in variant_and_legacy_folders + toolchain_paths:
            folder.mkdir(parents=True, exist_ok=True)

    def create_legacy_make_variables_dump_file(self) -> None:
        # include the legacy makefile and save all make variables
        self.run_collect_mak()

    def run_collect_mak(self):
        subprocess.run(
            [
                WindowsPath("src/collect.bat"),
                self.config.input_dir,
                self.config.output_dir,
                self.config.build_dir_rel,
                self.config.variant.to_string(),
            ]
        )

    def copy_vscode_files(self):
        copy_tree("src/dist", self.config.output_dir)

    def copy_source_files(self):
        mirror_tree(
            self.config.input_dir / self.config.source_dir_rel,
            self.config.output_dir / f"legacy/{self.config.variant}/src",
        )

    def copy_linker_definition(self):
        bld_cfg_out = self.variant_dir / "Bld/Cfg"
        mirror_tree(self.config.input_dir / "Impl/Bld/Cfg", bld_cfg_out)
        for path, _, files in os.walk(os.path.abspath(bld_cfg_out)):
            for filename in files:
                filepath = os.path.join(path, filename)
                with open(filepath) as f:
                    try:
                        s = f.read()
                    except:
                        print(
                            f"WARNING: Could not read file: {filepath}. This is most likely a binary file."
                        )
                        continue
                s = s.replace(
                    "../../Src", f"../../../../../legacy/{self.config.variant}/src"
                )
                with open(filepath, "w") as f:
                    f.write(s)

    def copy_config(self):
        config_out = self.variant_dir / "Cfg"
        mirror_tree(self.config.input_dir / "Impl/Cfg", config_out)
        for filename in glob.glob(
            os.path.abspath(config_out) + "/**/*.bat", recursive=True
        ):
            with open(filename) as f:
                s = f.read()
            s = s.replace(
                "start ..\\..\\..\\ThirdParty\\CBD\\",
                "start ..\\..\\..\\..\\..\\build\\deps\\CBD123456\\",
            )
            with open(filename, "w") as f:
                f.write(s)
        for filename in glob.glob(
            os.path.abspath(config_out) + "/**/*.dpa", recursive=True
        ):
            with open(filename) as f:
                s = f.read()
            s = s.replace(">.\\", ">")
            s = s.replace(
                ">..\\..\\..\\ThirdParty\CBD\\",
                ">..\\..\\..\\..\\..\\build\\deps\\CBD123456\\",
            )
            s = s.replace(
                ">..\..\..\ThirdParty\CBD<",
                ">..\\..\\..\\..\\..\\build\\deps\\CBD123456<",
            )
            legacy_gen_data = f"legacy\\{self.config.variant.flavor}\\{self.config.variant.subsystem}\\Bsw\\GenData"
            s = s.replace(
                ">..\..\Src\Bsw\GenData\\", f">..\\..\\..\\..\\..\\{legacy_gen_data}\\"
            )
            s = s.replace(
                ">..\..\Src\Bsw\GenData<",
                f">..\\..\\..\\..\\..\\{legacy_gen_data}<",
            )
            with open(filename, "w") as f:
                f.write(s)

    def copy_libs(self):
        mirror_tree(
            self.config.input_dir / "ThirdParty/customer1",
            self.variant_dir / "Lib/customer1",
            ["*.lib", "*.a"],
        )
        mirror_tree(
            self.config.input_dir / "ThirdParty/customer2",
            self.variant_dir / "Lib/customer2",
            ["*.lib", "*.a"],
        )

    def create_variant_json(self, variant: Variant = None):
        if not variant:
            variant = self.config.variant
        (self.config.output_dir / ".vscode").mkdir(parents=True, exist_ok=True)
        file = Path(self.config.output_dir / ".vscode/cmake-variants.json")
        if os.path.isfile(file):
            with open(file, "r") as f:
                data = json.loads(f.read())
            with open(file, "w") as f:
                new_entry = {f"{variant}": self.create_vs_code_variant_config(variant)}
                data["variant"]["choices"].update(new_entry)
                f.write(json.dumps(data, indent=2, sort_keys=True) + "\n")
        else:
            with open(file, "w") as f:
                f.write(
                    json.dumps(
                        {
                            "variant": {
                                "default": f"{variant}",
                                "choices": {
                                    f"{variant}": self.create_vs_code_variant_config(
                                        variant
                                    )
                                },
                            }
                        },
                        indent=2,
                        sort_keys=True,
                    )
                    + "\n"
                )

    def create_vs_code_variant_config(self, variant: Variant):
        return {
            "short": f"{variant}",
            "long": f"select to build variant '{variant}'",
            "buildType": variant.to_string("_"),
            "settings": {
                "FLAVOR": variant.flavor,
                "SUBSYSTEM": variant.subsystem,
            },
        }


def mirror_tree(source, target, patterns=[]):
    subprocess.run(
        ["robocopy", source, target] + patterns + ["/PURGE", "/S"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )
    for p in Path(target).glob("**/.dm"):
        shutil.rmtree(p)


def copy_tree(source, target, patterns=[]):
    subprocess.run(
        ["robocopy", source, target] + patterns + ["/XC", "/XN", "/XO", "/S"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )
    for p in Path(target).glob("**/.dm"):
        shutil.rmtree(p)


def create_argument_parser(argv=None):
    arguments = docopt(__doc__, argv)
    return arguments


def main() -> int:
    arguments = create_argument_parser()
    if arguments["--config"]:
        config = TransformerConfig.from_json_file(Path(arguments["--config"]))
    else:
        config = TransformerConfig(
            Path(arguments["--source"]),
            Path(arguments["--target"]),
            Variant.from_str(arguments["--variant"]),
        )
    Transformer(config).run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
