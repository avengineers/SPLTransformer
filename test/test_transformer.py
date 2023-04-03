#!/usr/bin/env python3

import os
import stat
import subprocess
import tempfile
import textwrap
import unittest
import shutil
from docopt import DocoptExit

import pytest
from LegacyBuildSystem import LegacyBuildSystem
from TransformerConfig import DirMirrorData, TransformerConfig
from Variant import Variant
from transformer import (
    Transformer,
    create_argument_parser,
)
from pathlib import Path


def handle_remove_readonly(func, path, exc_info):
    # Check if the error is due to read-only access
    if not os.access(path, os.W_OK):
        # Change the file attributes to allow write access and try to remove the file again
        os.chmod(path, stat.S_IWRITE)
        func(path)
    else:
        raise


@pytest.fixture
def new_transformer(request) -> Transformer:
    output_dir = Path("output/test")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create a temporary directory inside the output directory
    tmp_path = Path(tempfile.mkdtemp(dir=output_dir)).absolute()
    project_name = request.param if request.param else "prj1"
    variant = Variant("MY", "VAR")
    transformer = Transformer(
        TransformerConfig(
            Path(f"test/data/{project_name}").absolute(), tmp_path, variant
        )
    )

    # Return the path to the temporary directory
    yield transformer

    # Clean up the temporary directory after the test is done
    shutil.rmtree(tmp_path, onerror=handle_remove_readonly)


class TestTransformer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None
        cls.in_path = Path("test/data/prj1").absolute()
        cls.out_path = Path("output/test").absolute()
        cls.variant = Variant("MQ_123", "TEST")
        cls.transformer = Transformer(
            TransformerConfig(
                cls.in_path.resolve(), cls.out_path.resolve(), cls.variant
            )
        )
        try:
            shutil.rmtree(cls.out_path)
        except:
            print("Nothing to clean up.")

    def test_variant_json_creation(self):
        """will create a new json if not existing"""
        variant_file = TestTransformer.out_path / ".vscode/cmake-variants.json"
        try:
            variant_file.unlink()
        except:
            pass
        TestTransformer.transformer.create_variant_json(Variant("Variant_1", "sub1"))
        self.assertTrue(variant_file.exists())

        self.assertEqual(
            variant_file.read_text(),
            """{
  "variant": {
    "choices": {
      "Variant_1/sub1": {
        "buildType": "Variant_1_sub1",
        "long": "select to build variant 'Variant_1/sub1'",
        "settings": {
          "FLAVOR": "Variant_1",
          "SUBSYSTEM": "sub1"
        },
        "short": "Variant_1/sub1"
      }
    },
    "default": "Variant_1/sub1"
  }
}
""",
        )

        """will add a new entry if existing"""
        self.assertTrue(variant_file.exists())
        TestTransformer.transformer.create_variant_json()
        self.assertEqual(
            variant_file.read_text(),
            """{
  "variant": {
    "choices": {
      "MQ_123/TEST": {
        "buildType": "MQ_123_TEST",
        "long": "select to build variant 'MQ_123/TEST'",
        "settings": {
          "FLAVOR": "MQ_123",
          "SUBSYSTEM": "TEST"
        },
        "short": "MQ_123/TEST"
      },
      "Variant_1/sub1": {
        "buildType": "Variant_1_sub1",
        "long": "select to build variant 'Variant_1/sub1'",
        "settings": {
          "FLAVOR": "Variant_1",
          "SUBSYSTEM": "sub1"
        },
        "short": "Variant_1/sub1"
      }
    },
    "default": "Variant_1/sub1"
  }
}
""",
        )

    @unittest.skip("Build environment created by bootstrap.")
    def test_transform_and_build_test_project(self):
        """Transformed project shall be buildable"""
        TestTransformer.transformer.run()
        process = subprocess.run(
            [
                str(TestTransformer.out_path / "build.bat"),
                "--build",
                "--target",
                "all",
                "--variants",
                TestTransformer.variant,
            ]
        )
        self.assertEqual(0, process.returncode)
        self.assertTrue(
            (
                TestTransformer.out_path
                / f"build/{TestTransformer.variant}/prod/main.exe"
            )
        ).exists()


def test_argument_parser():
    arg_list = ["--config", "C:/my_file"]
    parsed_args = create_argument_parser(arg_list)
    assert parsed_args["--config"] == "C:/my_file"


def test_argument_parser_mutually_exclusive_arguments():
    arg_list = ["--config", "C:/my_file", "--source", "C:/input"]
    with pytest.raises(DocoptExit):
        create_argument_parser(arg_list)


@pytest.mark.parametrize("new_transformer", ["prj1"], indirect=True)
def test_cmake_project_creation(new_transformer: Transformer):
    transformer = new_transformer
    transformer.create_cmake_project(LegacyBuildSystem("", transformer.config))

    out_dir = transformer.output_dir
    variant = transformer.variant

    for file in [
        out_dir.joinpath(f"variants/{variant}/parts.cmake"),
        out_dir.joinpath(f"variants/{variant}/config.cmake"),
        out_dir.joinpath(f"legacy/{variant}/parts.cmake"),
        out_dir.joinpath(f"legacy/CMakeLists.txt"),
    ]:
        assert file.is_file()


@pytest.mark.parametrize("new_transformer", ["prj1"], indirect=True)
def test_mirror_directories(new_transformer: Transformer):
    transformer = new_transformer
    transformer.config.mirror_directories = [
        DirMirrorData(Path("Impl/Bld"), Path("NewBld"))
    ]
    transformer.mirror_directories()

    out_dir = transformer.output_dir

    for file in [
        out_dir.joinpath("NewBld/makefile"),
        out_dir.joinpath("NewBld/Cfg/Linker.ld"),
        out_dir.joinpath("NewBld/Cfg/binary_file.so"),
    ]:
        assert file.is_file()


@pytest.mark.parametrize("new_transformer", ["prj1"], indirect=True)
def test_create_legacy_make_variables_dump_file(new_transformer: Transformer):
    transformer = new_transformer
    transformer.config.batch_commands = ["set TESTVAR=BLAFASEL"]
    transformer.variant_dir.mkdir(parents=True, exist_ok=True)
    transformer.create_legacy_make_variables_dump_file()

    assert transformer.variant_dir.joinpath("original_make_vars.txt").is_file()
    assert transformer.variant_dir.joinpath("collect.bat").is_file()
    assert transformer.variant_dir.joinpath("collect.mak").is_file()

    assert (
        "TESTVAR = BLAFASEL"
        in transformer.variant_dir.joinpath("original_make_vars.txt").read_text()
    )
