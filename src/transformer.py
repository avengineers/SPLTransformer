#!/usr/bin/env python3

"""Transformer

Usage:
  transformer.py (--source=<source directory> --target=<target directory> --variant=<variant> | --config=<config_file>)
  transformer.py (-h | --help)

Options:
  -h --help        Show this screen.
  --source=DIR     Source directory holding a Dimensions make project
  --target=DIR     Target directory for the transformed CMake project
  --variant=VARIANT  VARIANT of the transformed CMake project (e.g., 'customer1_subsystem_flavor')
  --config=FILE    JSON configuration file

"""

from dataclasses import dataclass
import glob
from typing import Dict, Optional
import dacite
from docopt import docopt
import logging
import subprocess
import shutil
import os
from pathlib import WindowsPath, Path
import json


@dataclass
class TransformerConfig:
    input_dir: Path
    output_dir: Path
    variant: str
    sources: Optional[str] = None

    @classmethod
    def from_json_file(cls, file: Path):
        json_data = cls.read_json(file)
        return dacite.from_dict(
            data_class=cls,
            data=json_data,
            config=dacite.Config(
                type_hooks={Path: lambda data: Path(data) if data else None}
            ),
        )

    @staticmethod
    def read_json(config_json_file: Path) -> Dict:
        if config_json_file is None:
            return {}
        with open(config_json_file, "r") as f:
            data = json.load(f)
        return data


class Transformer:
    def __init__(
        self,
        config: TransformerConfig,
    ):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.name = "Transformer"
        self.config: Optional[TransformerConfig] = config

        self.impl_out_path = self.out_path
        self.impl_in_path = self.in_path / "Impl"
        self.build_in_path = self.impl_in_path / "Bld"

    @property
    def in_path(self) -> Path:
        return self.config.input_dir

    @property
    def out_path(self) -> Path:
        return self.config.output_dir

    @property
    def variant(self) -> str:
        return self.config.variant

    def run(self):
        self.copy_source_files()
        self.copy_libs()
        self.copy_build_wrapper_files()
        self.create_cmake_project()
        self.copy_linker_definition()
        self.copy_config()
        self.create_variant_json()

    def create_cmake_project(self):
        self.logger.info("create project file")
        (self.out_path / "variants" / self.variant).mkdir(parents=True, exist_ok=True)
        (self.out_path / "legacy" / self.variant).mkdir(parents=True, exist_ok=True)
        (self.out_path / "tools/toolchains/gcc").mkdir(parents=True, exist_ok=True)
        (self.out_path / "tools/toolchains/comp_201754").mkdir(
            parents=True, exist_ok=True
        )
        (self.out_path / "tools/toolchains/comp_201914").mkdir(
            parents=True, exist_ok=True
        )
        (self.out_path / "tools/toolchains/TriCore_v6p2r2p2").mkdir(
            parents=True, exist_ok=True
        )
        (self.out_path / "tools/toolchains/TriCore_v6p3r1").mkdir(
            parents=True, exist_ok=True
        )

        # run twice to get properties file first
        self.run_collect_mak()

        variant_parts_path = self.out_path / "variants" / self.variant / "parts.cmake"
        with open(variant_parts_path, "a") as f:
            for root, dirs, files in os.walk(
                self.out_path / "variants" / self.variant / "Lib"
            ):
                for file in files:
                    print(file)
                    if file.endswith(".a") or file.endswith(".lib"):
                        rel_path = os.path.relpath(
                            os.path.join(root, file),
                            self.out_path / "variants" / self.variant,
                        ).replace("\\", "/")
                        f.write(
                            "target_link_libraries(${{LINK_TARGET_NAME}} ${{CMAKE_CURRENT_LIST_DIR}}/{})\n".format(
                                rel_path
                            )
                        )

    def run_collect_mak(self):
        subprocess.run(
            [
                WindowsPath("src/collect.bat"),
                self.build_in_path,
                self.out_path,
                self.variant,
            ]
        )

    def copy_build_wrapper_files(self):
        copy_tree("src/dist", self.out_path)

    def copy_source_files(self):
        mirror_tree(self.in_path / "Impl/Src", self.out_path / "legacy" / self.variant)

    def copy_linker_definition(self):
        bld_cfg_out = self.out_path / "variants" / self.variant / "Bld/Cfg"
        mirror_tree(self.in_path / "Impl/Bld/Cfg", bld_cfg_out)
        for path, dirs, files in os.walk(os.path.abspath(bld_cfg_out)):
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
                s = s.replace("../../Src", "../../../../../legacy/" + self.variant)
                with open(filepath, "w") as f:
                    f.write(s)

    def copy_config(self):
        config_out = self.out_path / "variants" / self.variant / "Cfg"
        mirror_tree(self.in_path / "Impl/Cfg", config_out)
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
            s = s.replace(
                ">..\..\Src\Bsw\GenData\\",
                ">..\\..\\..\\..\\..\\legacy\\{variant}\\Bsw\\GenData\\".format(
                    variant=self.variant.replace("/", "\\")
                ),
            )
            s = s.replace(
                ">..\..\Src\Bsw\GenData<",
                ">..\\..\\..\\..\\..\\legacy\\{variant}\\Bsw\\GenData<".format(
                    variant=self.variant.replace("/", "\\")
                ),
            )
            with open(filename, "w") as f:
                f.write(s)

    def copy_libs(self):
        mirror_tree(
            self.in_path / "ThirdParty/customer1",
            self.out_path / "variants" / self.variant / "Lib/customer1",
            ["*.lib", "*.a"],
        )
        mirror_tree(
            self.in_path / "ThirdParty/customer2",
            self.out_path / "variants" / self.variant / "Lib/customer2",
            ["*.lib", "*.a"],
        )

    def create_variant_json(self, variant=""):
        if not variant:
            variant = self.variant
        (self.out_path / ".vscode").mkdir(parents=True, exist_ok=True)
        file = Path(self.out_path / ".vscode/cmake-variants.json")
        flavor, subsystem = variant.split("/")
        if os.path.isfile(file):
            with open(file, "r") as f:
                data = json.loads(f.read())
            with open(file, "w") as f:
                new_entry = {
                    "{}".format(variant): {
                        "short": variant,
                        "long": "select to build variant '{}'".format(variant),
                        "buildType": flavor + "_" + subsystem,
                        "settings": {"FLAVOR": flavor, "SUBSYSTEM": subsystem},
                    }
                }
                data["variant"]["choices"].update(new_entry)
                f.write(json.dumps(data, indent=2, sort_keys=True) + "\n")
        else:
            with open(file, "w") as f:
                f.write(
                    json.dumps(
                        {
                            "variant": {
                                "default": variant,
                                "choices": {
                                    "{}".format(variant): {
                                        "short": variant,
                                        "long": "select to build variant '"
                                        + variant
                                        + "'",
                                        "buildType": flavor + "_" + subsystem,
                                        "settings": {
                                            "FLAVOR": flavor,
                                            "SUBSYSTEM": subsystem,
                                        },
                                    }
                                },
                            }
                        },
                        indent=2,
                        sort_keys=True,
                    )
                    + "\n"
                )


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


def main():
    arguments = create_argument_parser()
    transformer = Transformer(
        TransformerConfig(
            Path(arguments["--source"]),
            Path(arguments["--target"]),
            arguments["--variant"],
        )
    )
    transformer.run()
    return 0


if __name__ == "__main__":
    main()
