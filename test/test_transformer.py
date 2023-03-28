#!/usr/bin/env python3

import os
import subprocess
import tempfile
import textwrap
import unittest
import shutil
from docopt import DocoptExit

import pytest
from transformer import (
    LegacyBuildSystem,
    TransformerConfig,
    Transformer,
    Variant,
    create_argument_parser,
)
from pathlib import Path


@pytest.fixture
def new_transformer(request) -> Transformer:
    output_dir = Path("output/test")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create a temporary directory inside the output directory
    tmp_path = Path(tempfile.mkdtemp(dir=output_dir))
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
    shutil.rmtree(tmp_path)


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

    def test_copy_build_wrapper_files(self):
        """Build wrapper shall be created."""
        TestTransformer.transformer.copy_vscode_files()
        self.assertTrue((TestTransformer.out_path / "CMakeLists.txt").exists())
        self.assertTrue(
            (TestTransformer.out_path / "tools/toolchains/gcc/toolchain.cmake").exists()
        )
        self.assertTrue((TestTransformer.out_path / ".vscode/cmake-kits.json").exists())

    def test_copy_linker_definition(self):
        """Linker definition files shall be copied."""
        TestTransformer.transformer.copy_linker_definition()
        self.assertTrue(
            (
                TestTransformer.out_path
                / f"variants/{TestTransformer.variant}/Bld/Cfg/Linker.ld"
            ).exists()
        )

    def test_copy_config(self):
        """Variant specific configuration shall be copied."""
        TestTransformer.transformer.copy_config()
        eb_tresos_start_script = (
            TestTransformer.out_path
            / "variants"
            / f"{TestTransformer.variant}"
            / "Cfg/MCAL/EB-Tresos.bat"
        )
        self.assertTrue(eb_tresos_start_script.exists())
        content = eb_tresos_start_script.read_text()
        self.assertIn("start ..\\..\\..\\..\\..\\build\\deps\\CBD123456", content)
        davinci_project_file = (
            TestTransformer.out_path
            / "variants"
            / f"{TestTransformer.variant}"
            / "Cfg/Autosar/HV_Sensor.dpa"
        )
        self.assertTrue(davinci_project_file.exists())
        content = davinci_project_file.read_text()
        self.assertNotIn(">.\\<", content)
        self.assertNotIn(">..\\..\\..\\ThirdParty\\CBD", content)
        self.assertNotIn(">..\\..\\Src\\Bsw\\GenData\\", content)
        self.assertNotIn(">.\\..\\..\\Src\\Bsw\\GenData\\", content)
        self.assertIn(">..\\..\\..\\..\\..\\build\\deps\\CBD123456", content)
        self.assertIn(
            ">..\\..\\..\\..\\..\\legacy\\{variant}\\Bsw\\GenData".format(
                variant=TestTransformer.variant.to_string("\\")
            ),
            content,
        )

    def test_copy_libs(self):
        """Libraries shall be copied."""
        TestTransformer.transformer.copy_libs()
        self.assertTrue(
            (
                TestTransformer.out_path
                / f"variants/{TestTransformer.variant}"
                / "Lib/customer1/libspl.a"
            ).exists()
        )

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


@pytest.mark.parametrize(
    "input_dir,output_dir,source_dir_rel",
    [
        ("test/data/prj1", "output/test/prj1", None),
        ("test/data/prj2", "output/test/prj2", "Implementation/Src"),
    ],
)
def test_copy_source_files(input_dir, output_dir, source_dir_rel):
    """Source files shall be copied."""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    variant = "MY/VAR"
    argdict = {"input_dir": input_path, "output_dir": output_path, "variant": variant}
    if source_dir_rel:
        argdict["source_dir_rel"] = source_dir_rel
    transformer = Transformer(TransformerConfig(**argdict))
    transformer.copy_source_files()

    files_to_check = [
        f"legacy/{variant}/src/main.c",
        f"legacy/{variant}/src/component_a/component_a.c",
        f"legacy/{variant}/src/component_a/component_a.h",
        f"legacy/{variant}/src/include_dir/header.h",
    ]

    for file_path in files_to_check:
        assert (output_path / file_path).exists()


@pytest.mark.parametrize("new_transformer", ["prj1"], indirect=True)
def test_cmake_project_creation(new_transformer: Transformer):
    transformer = new_transformer
    transformer.copy_libs()
    transformer.create_cmake_project(LegacyBuildSystem("", transformer.config))

    out_dir = transformer.output_dir
    variant = transformer.variant

    for file in [
        out_dir.joinpath(f"variants/{variant}/parts.cmake"),
        out_dir.joinpath(f"legacy/{variant}/parts.cmake"),
        out_dir.joinpath(f"legacy/CMakeLists.txt"),
    ]:
        assert file.is_file()
