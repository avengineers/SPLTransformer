#!/usr/bin/env python3

"""Transformer

Usage:
  transformer.py (--source=<source directory> --target=<target directory> --variant=<variant> | --config=<config_file>) [--make-dump-file=<make_dump_file>]
  transformer.py (-h | --help)

Options:
  -h --help                 Show this screen.
  --source=DIR              Source directory holding a Dimensions make project
  --target=DIR              Target directory for the transformed CMake project
  --variant=VARIANT         VARIANT of the transformed CMake project (e.g., 'customer1_subsystem_flavor')
  --config=FILE             JSON configuration file
  --make-dump-file=FILE     Make dump file from previous run. This will avoid regenerating this file, which might take long time.
"""

import dataclasses
import sys
import textwrap
from typing import List, Optional
from docopt import docopt
import logging
import subprocess
import shutil
import os
from pathlib import WindowsPath, Path
import json
from TransformerConfig import DirMirrorData, TransformerConfig
from Variant import Variant
from LegacyBuildSystem import LegacyBuildSystem
from file_generators import (
    LegacyCMakeListsGenerator,
    LegacyPartsCMakeGenerator,
    VariantConfigCMakeGenerator,
    VariantPartsCMakeGenerator,
)


def this_script_dir() -> Path:
    return Path(__file__).parent


class Transformer:
    def __init__(self, config: TransformerConfig, make_dump_file: Optional[str] = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.name = type(self).__name__
        self.config: TransformerConfig = config
        self.make_dump_file: Path = (
            Path(make_dump_file)
            if make_dump_file
            else self.variant_dir / "original_make_vars.txt"
        )
        self.execution_summary: List[str] = []

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
    def variant_parts_cmake_file(self) -> Path:
        return self.variant_dir / "parts.cmake"

    @property
    def variant_config_cmake_file(self) -> Path:
        return self.variant_dir / "config.cmake"

    @property
    def legacy_parts_cmake_file(self) -> Path:
        return self.legacy_variant_dir / "parts.cmake"

    @property
    def legacy_cmake_lists_file(self) -> Path:
        return self.legacy_dir / "CMakeLists.txt"

    def run(self):
        if not self.input_dir.exists():
            raise FileNotFoundError(f"Input directory {self.input_dir} does not exist.")
        self.create_folder_structure()
        self.create_legacy_make_variables_dump_file()
        self.mirror_directories()
        self.create_cmake_project(LegacyBuildSystem(self.make_dump_file, self.config))
        self.create_variant_json()
        self.print_execution_summary()

    def create_cmake_project(self, legacy_build_system: LegacyBuildSystem) -> None:
        VariantPartsCMakeGenerator(
            legacy_build_system.get_include_paths(),
            legacy_build_system.get_thirdparty_libs(),
            self.config.subdir_replacements,
        ).to_file(self.variant_parts_cmake_file)
        self.add_execution_summary(
            f"variant parts cmake {self.variant_parts_cmake_file.relative_to(self.output_dir)}"
        )

        VariantConfigCMakeGenerator(
            self.config.variant_compiler_flags,
            self.config.variant_linker_file,
            self.config.variant_link_flags,
            self.config.cmake_toolchain_file,
        ).to_file(self.variant_config_cmake_file)
        self.add_execution_summary(
            f"variant config cmake {self.variant_config_cmake_file.relative_to(self.output_dir)}"
        )
        LegacyPartsCMakeGenerator(
            legacy_build_system.get_source_paths(),
            self.config.subdir_replacements,
        ).to_file(self.legacy_parts_cmake_file)
        self.add_execution_summary(
            f"legacy parts cmake {self.legacy_parts_cmake_file.relative_to(self.output_dir)}"
        )
        LegacyCMakeListsGenerator().to_file(self.legacy_cmake_lists_file)
        self.add_execution_summary(
            f"legacy cmake listing {self.legacy_cmake_lists_file.relative_to(self.output_dir)}"
        )

    def create_folder_structure(self) -> None:
        variant_and_legacy_folders = [self.variant_dir, self.legacy_variant_dir]
        toolchain_folders = ["tools/toolchains/gcc"]

        toolchain_paths = [
            self.config.output_dir.joinpath(folder) for folder in toolchain_folders
        ]

        for folder in variant_and_legacy_folders + toolchain_paths:
            folder.mkdir(parents=True, exist_ok=True)

    def mirror_directories(self):
        mirror_dirs_data = self.config.mirror_directories + [
            DirMirrorData(
                this_script_dir().joinpath("dist"), self.output_dir, mirror=False
            )
        ]
        for dir_mirror_data in mirror_dirs_data:
            resolved_data = dataclasses.replace(dir_mirror_data)
            resolved_data.source = self.input_dir.joinpath(dir_mirror_data.source)
            resolved_data.target = self.output_dir.joinpath(dir_mirror_data.target)
            mirror_tree(resolved_data)
            self.add_execution_summary(
                f"Copied from {resolved_data.source} to {resolved_data.target}"
            )

    def create_legacy_make_variables_dump_file(self) -> None:
        if self.make_dump_file.is_file():
            print(
                f"Skipping make dump file generation, using already existing {self.make_dump_file}."
            )
            return
        self.add_execution_summary(
            f"Generating make file dump to {self.make_dump_file.relative_to(self.output_dir)}."
        )

        collect_bat = self.variant_dir.joinpath("collect.bat")
        collect_bat.write_text(
            "\n".join(
                [
                    "@echo on",
                    "set THIS_DIR=%~dp0",
                    f"set MAKE_VARS_FILE={str(self.make_dump_file)}",
                    f"pushd {self.config.input_dir / self.config.build_dir_rel}",
                ]
                + self.config.batch_commands
                + [
                    "@echo on",
                    "where make",
                    "make --silent --file=%THIS_DIR%collect.mak collect",
                    "popd",
                ]
            )
        )

        collect_mak = self.variant_dir.joinpath("collect.mak")
        shutil.copy(Path("src/collect.mak"), collect_mak)

        subprocess.run([WindowsPath(collect_bat).absolute()])

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

    def print_execution_summary(self):
        todos = [f"Create a toolchain file for your compiler or use an existing one."]
        print(
            f"Variant {self.variant} generated from legacy project {self.input_dir} into {self.output_dir}"
        )
        print("Execution summary:")
        for done in self.execution_summary:
            print(f" - [x] {done}")

        print("TODOs:")
        for todo in todos:
            print(f" - [ ] {todo}")

    def add_execution_summary(self, description: str) -> None:
        self.execution_summary.append(description)


def mirror_tree(dir_mirror_data: DirMirrorData) -> None:
    robocopy_params = (
        ["/PURGE", "/S"] if dir_mirror_data.mirror else ["/XC", "/XN", "/XO", "/S"]
    )
    subprocess.run(
        ["robocopy", dir_mirror_data.source, dir_mirror_data.target]
        + dir_mirror_data.patterns
        + robocopy_params,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )
    for p in Path(dir_mirror_data.target).glob("**/.dm"):
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
    Transformer(config, arguments["--make-dump-file"]).run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
