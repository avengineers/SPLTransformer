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

import glob
import sys
from typing import List, Optional
from docopt import docopt
import logging
import subprocess
import shutil
import os
from pathlib import WindowsPath, Path
import json
from TransformerConfig import TransformerConfig
from Variant import Variant
from LegacyBuildSystem import LegacyBuildSystem
from file_generators import (
    LegacyCMakeListsGenerator,
    LegacyPartsCMakeGenerator,
    VariantConfigCMakeGenerator,
    VariantPartsCMakeGenerator,
)


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
        self.copy_source_files()
        self.copy_libs()
        self.copy_vscode_files()
        self.create_cmake_project(LegacyBuildSystem(self.make_dump_file, self.config))
        self.copy_linker_definition()
        self.copy_config()
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

    def create_legacy_make_variables_dump_file(self) -> None:
        if self.make_dump_file.is_file():
            print(
                f"Skipping make dump file generation, using already existing {self.make_dump_file}."
            )
            return
        self.add_execution_summary(
            f"Generating make file dump to {self.make_dump_file.relative_to(self.output_dir)}."
        )

        # include the legacy makefile and save all make variables
        self.run_collect_mak()

    def run_collect_mak(self):
        # Create a copy of the current environment variables
        current_env = os.environ.copy()
        # Add or modify environment variables
        current_env["MAKESUPPORT_DIR"] = str(
            self.config.input_dir / "COMMON/CBD/MakeSupport"
        )
        current_env["MAKE_VARS_FILE"] = str(self.make_dump_file)
        subprocess.run(
            [WindowsPath("src/collect.bat").absolute()],
            cwd=self.config.input_dir / self.config.build_dir_rel,
            env=current_env,
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


def mirror_tree(source: Path, target: Path, patterns=[]):
    subprocess.run(
        ["robocopy", source, target] + patterns + ["/PURGE", "/S"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )
    for p in Path(target).glob("**/.dm"):
        shutil.rmtree(p)


def copy_tree(source: Path, target: Path, patterns=[]):
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
    Transformer(config, arguments["--make-dump-file"]).run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
