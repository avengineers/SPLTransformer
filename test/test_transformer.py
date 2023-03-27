#!/usr/bin/env python3

import os
import subprocess
import tempfile
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
from utils import read_file


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
    tmp_path.rmtree()


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
        content = read_file(eb_tresos_start_script)
        self.assertIn("start ..\\..\\..\\..\\..\\build\\deps\\CBD123456", content)
        davinci_project_file = (
            TestTransformer.out_path
            / "variants"
            / f"{TestTransformer.variant}"
            / "Cfg/Autosar/HV_Sensor.dpa"
        )
        self.assertTrue(davinci_project_file.exists())
        content = read_file(davinci_project_file)
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
        f"legacy/{variant}/main.c",
        f"legacy/{variant}/component_a/component_a.c",
        f"legacy/{variant}/component_a/component_a.h",
        f"legacy/{variant}/include_dir/header.h",
    ]

    for file_path in files_to_check:
        assert (output_path / file_path).exists()


@pytest.mark.parametrize("new_transformer", ["prj1"], indirect=True)
def test_cmake_project_creation(new_transformer: Transformer):
    transformer = new_transformer
    out_path = transformer.output_dir
    variant = transformer.variant

    make_dump = "CPPFLAGS_INC_LIST = -I../../MQ_123/TEST/component_a -I../../MQ_123/TEST/include_dir"

    transformer.copy_libs()
    transformer.create_cmake_project(LegacyBuildSystem(make_dump, transformer.config))

    cmake_list_file = transformer.variant_dir / "parts.cmake"
    assert cmake_list_file.is_file()
    cmake_file_content = read_file(cmake_list_file)
    assert (
        """# Generated by Transformer
spl_add_include(${PROJECT_SOURCE_DIR}/legacy/${VARIANT}/MQ_123/TEST/component_a)
spl_add_include(${PROJECT_SOURCE_DIR}/legacy/${VARIANT}/MQ_123/TEST/include_dir)

spl_add_component(legacy/MY/VAR)
target_link_libraries(${LINK_TARGET_NAME} ${CMAKE_CURRENT_LIST_DIR}/Lib/AnyAG/libspl.a)
target_link_libraries(${LINK_TARGET_NAME} ${CMAKE_CURRENT_LIST_DIR}/Lib/customer1/libspl.a)
"""
        == cmake_file_content
    )

    toolchain_cmake_file = out_path / "tools/toolchains/gcc/toolchain.cmake"
    assert toolchain_cmake_file.is_file()
    toolchain_cmake_content = read_file(toolchain_cmake_file)
    scoop_dir = os.environ["USERPROFILE"] + "/scoop"
    if "SCOOP" in os.environ:
        scoop_dir = os.environ["SCOOP"]
    assert (
        """# Generated by Transformer
set(CMAKE_C_COMPILER "{scoop_dir}/apps/gcc-llvm_11p2p0-13p0p0/11.2.0-13.0.0-9.0.0-r3/bin/gcc.exe")
set(CMAKE_CXX_COMPILER ${{CMAKE_C_COMPILER}})
set(CMAKE_ASM_COMPILER "{scoop_dir}/apps/gcc-llvm_11p2p0-13p0p0/11.2.0-13.0.0-9.0.0-r3/bin/gcc.exe")
set(CMAKE_C_DEPFILE_EXTENSION_REPLACE 1)
set(CMAKE_ASM_DEPFILE_EXTENSION_REPLACE 1)

set(COMPILE_C_FLAGS -DKARSTEN -DMATTHIAS -DALEXANDER)
set(COMPILE_ASM_FLAGS -DFoo -DALEXANDER)
add_compile_options(
    "$<$<COMPILE_LANGUAGE:C>:${{COMPILE_C_FLAGS}}>"
    "$<$<COMPILE_LANGUAGE:ASM>:${{COMPILE_ASM_FLAGS}}>"
)
add_link_options(-Dp=./blablub)
""".format(
            scoop_dir=scoop_dir.replace("\\", "/")
        )
        == toolchain_cmake_content
    )

    cmake_legacy_list_file = out_path / "legacy" / variant / "CMakeLists.txt"
    assert cmake_legacy_list_file.is_file()
    cmake_file_content = read_file(cmake_legacy_list_file)
    assert (
        """# Generated by Transformer
include(parts.cmake)
spl_create_component()
"""
        == cmake_file_content
    )

    cmake_legacy_parts_file = out_path / "legacy" / variant / "parts.cmake"
    assert cmake_legacy_parts_file.is_file()
    cmake_file_content = read_file(cmake_legacy_parts_file)
    assert (
        """# Generated by Transformer
spl_add_source(main.c)
spl_add_source(component_a/component_a.c)
"""
        == cmake_file_content
    )
