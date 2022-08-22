#!/usr/bin/env python3

import os
import subprocess
import unittest
import shutil
from transformer import Transformer
from pathlib import Path
from utils import read_file


class TestTransformer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None
        cls.in_path = Path('test/data')
        cls.out_path = Path('output/test')
        cls.variant = 'MQ_123/TEST'
        cls.transformer = Transformer(
            cls.in_path.resolve(),
            cls.out_path.resolve(),
            cls.variant
        )
        try:
            shutil.rmtree(cls.out_path)
        except:
            print('Nothing to clean up.')

    def test_cmake_project_creation(self):
        """CMake Project shall be created."""
        TestTransformer.transformer.copy_libs()
        TestTransformer.transformer.create_cmake_project()

        cmake_list_file = TestTransformer.out_path / \
            'variants' / TestTransformer.variant / 'parts.cmake'
        self.assertTrue(cmake_list_file.is_file())
        cmake_file_content = read_file(cmake_list_file)
        self.assertEquals(
            '''# Generated by Transformer
add_include(/legacy/MQ_123/TEST/component_a)
add_include(/legacy/MQ_123/TEST/include_dir)

add_component(legacy/{output_name})
target_link_libraries(${{ELF_TARGET_NAME}} ${{CMAKE_CURRENT_LIST_DIR}}/Lib/customer1/libspl.a)
target_link_libraries(${{ELF_TARGET_NAME}} ${{CMAKE_CURRENT_LIST_DIR}}/Lib/PAG/libspl.a)
'''.format(output_name=TestTransformer.variant), cmake_file_content)

        toolchain_cmake_file = TestTransformer.out_path / \
            'tools/toolchains/gcc/toolchain.cmake'.format(
                TestTransformer.variant)
        self.assertTrue(toolchain_cmake_file.is_file())
        toolchain_cmake_content = read_file(toolchain_cmake_file)
        scoop_dir = os.environ['USERPROFILE'] + '/scoop'
        if "SCOOP" in os.environ:
            scoop_dir = os.environ['SCOOP']
        self.assertEquals(
            '''# Generated by Transformer
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
'''.format(scoop_dir=scoop_dir.replace('\\', '/')), toolchain_cmake_content)

        cmake_legacy_list_file = TestTransformer.out_path / \
            'legacy' / TestTransformer.variant / 'CMakeLists.txt'
        self.assertTrue(cmake_legacy_list_file.is_file())
        cmake_file_content = read_file(cmake_legacy_list_file)
        self.assertEquals(
            '''# Generated by Transformer
include(parts.cmake)
create_component()
''', cmake_file_content)

        cmake_legacy_parts_file = TestTransformer.out_path / \
            'legacy' / TestTransformer.variant / 'parts.cmake'
        self.assertTrue(cmake_legacy_parts_file.is_file())
        cmake_file_content = read_file(cmake_legacy_parts_file)
        self.assertEquals(
            '''# Generated by Transformer
add_source(main.c)
add_source(component_a/component_a.c)
''', cmake_file_content)

    def test_copy_build_wrapper_files(self):
        """Build wrapper shall be created."""
        TestTransformer.transformer.copy_build_wrapper_files()
        self.assertTrue((TestTransformer.out_path / 'build.bat').exists())
        self.assertTrue((TestTransformer.out_path /
                        'CMakeLists.txt').exists())
        self.assertTrue((TestTransformer.out_path /
                        'install-mandatory.bat').exists())
        self.assertTrue((TestTransformer.out_path /
                        'install-optional.bat').exists())
        self.assertTrue((TestTransformer.out_path /
                        'tools/toolchains/gcc/toolchain.cmake').exists())

    def test_copy_source_files(self):
        """Source files shall be copied."""
        TestTransformer.transformer.copy_source_files()
        self.assertTrue((TestTransformer.out_path /
                        'legacy/MQ_123/TEST/main.c').exists())
        self.assertTrue((TestTransformer.out_path /
                        'legacy/MQ_123/TEST/component_a/component_a.c').exists())
        self.assertTrue((TestTransformer.out_path /
                        'legacy/MQ_123/TEST/component_a/component_a.h').exists())
        self.assertTrue((TestTransformer.out_path /
                        'legacy/MQ_123/TEST/include_dir/header.h').exists())

    def test_copy_linker_definition(self):
        """Linker definition files shall be copied."""
        TestTransformer.transformer.copy_linker_definition()
        self.assertTrue((TestTransformer.out_path /
                        'variants/{}/Bld/Cfg/Linker.ld'.format(TestTransformer.variant)).exists())

    def test_copy_config(self):
        """Variant specific configuration shall be copied."""
        TestTransformer.transformer.copy_config()
        eb_tresos_start_script = (
            TestTransformer.out_path / 'variants' /
            TestTransformer.variant / 'Cfg/MCAL/EB-Tresos.bat'
        )
        self.assertTrue(eb_tresos_start_script.exists())
        content = read_file(eb_tresos_start_script)
        self.assertIn('start ..\\..\\..\\..\\..\\build\\deps\\CBD123456', content)
        davinci_project_file = (
            TestTransformer.out_path / 'variants' /
            TestTransformer.variant / 'Cfg/Autosar/HV_Sensor.dpa'
        )
        self.assertTrue(davinci_project_file.exists())
        content = read_file(davinci_project_file)
        self.assertNotIn('>.\\<', content)
        self.assertNotIn('>..\\..\\..\\ThirdParty\\CBD', content)
        self.assertNotIn('>..\\..\\Src\\Bsw\\GenData\\', content)
        self.assertNotIn('>.\\..\\..\\Src\\Bsw\\GenData\\', content)
        self.assertIn('>..\\..\\..\\..\\..\\build\\deps\\CBD123456', content)
        self.assertIn('>..\\..\\..\\..\\..\\legacy\\{variant}\\Bsw\\GenData'.format(
            variant=TestTransformer.variant.replace('/', '\\')), content)

    def test_copy_libs(self):
        """Libraries shall be copied."""
        TestTransformer.transformer.copy_libs()
        self.assertTrue((TestTransformer.out_path /
                        'variants' / TestTransformer.variant / 'Lib/customer1/libspl.a').exists())

    def test_variant_json_creation(self):
        """will create a new json if not existing"""
        variant_file = TestTransformer.out_path / '.vscode/cmake-variants.json'
        try:
            variant_file.unlink()
        except:
            pass
        TestTransformer.transformer.create_variant_json('Variant_1/sub1')
        self.assertTrue(variant_file.exists())

        content = read_file(variant_file)
        self.assertEquals(content,
                          '''{
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
'''
                          )

        """will add a new entry if existing"""
        self.assertTrue(variant_file.exists())
        TestTransformer.transformer.create_variant_json()
        content = read_file(variant_file)
        self.assertEquals(content,
                          '''{
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
''')

#    def test_transform_and_build_test_project(self):
#        """Transformed project shall be buildable"""
#        TestTransformer.transformer.run()
#        process = subprocess.run(
#            [str(TestTransformer.out_path / 'build.bat'), '--build', '--target', 'default', '--variants', TestTransformer.variant])
#        self.assertEqual(0, process.returncode)
#        self.assertTrue((TestTransformer.out_path / 'build/{variant}/{variant_underscore}.elf'.format(
#            variant=TestTransformer.variant, variant_underscore=TestTransformer.variant.replace('/', '_'))).exists())
