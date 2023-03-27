from pathlib import Path

import pytest
from transformer import LegacyBuildSystem, TransformerConfig


def test_parse_make_variables_dump_file():
    content = """PIPENV_VERBOSITY = -1
<D = 
?F = 
ASFLAGS_CUSTOMER_OPTIONS = 
MY_INCLUDES = -I../ABC/path -I../IMPL/path
GENERATED_SOURCE_FILES = Impl\GenData\Rte.c Impl\GenData\ComXf.c Impl\GenData\E2EXf_LCfg.c
COMPILE.c = gcc
COMPILE.C = g++
AR_RULE = Output/lib/lib.a:   Output/lib/.dirstamp
	@echo "AR         lib.a"
ifeq (1,1)
	@echo " - sources:  "
endif
	@rm -f 
	 ./../COMMON/Compiler/ctc/bin/artc -cr Output/lib/lib.a  
"""
    make_dump = LegacyBuildSystem.parse_make_var_dump(content)
    assert len(make_dump.keys()) == 9
    assert make_dump["MY_INCLUDES"] == "-I../ABC/path -I../IMPL/path"
    assert make_dump["COMPILE.c"] == "gcc"
    assert make_dump["COMPILE.C"] == "g++"


def test_extract_include_paths():
    includes_str = "-I../ABC/path -I../IMPL/path"
    includes = LegacyBuildSystem.extract_include_paths(includes_str)
    assert includes == ["../ABC/path", "../IMPL/path"]


def test_extract_sources_path():
    sources_str = "   ../ABC/src.c ../IMPL/src.c    ../IMPL/src2.c"
    sources = LegacyBuildSystem.extract_source_paths(sources_str)
    assert sources == ["../ABC/src.c", "../IMPL/src.c", "../IMPL/src2.c"]


def test_get_includes():
    make_var_dump = "CPPFLAGS_INC_LIST = -I../ABC/bla -I../IMPL/foo"
    config = TransformerConfig(Path("X:/in"), Path("X:/out"), "my/var")
    config.build_dir_rel = "bld1/bld2"
    legacy_build = LegacyBuildSystem(make_var_dump, config)
    assert legacy_build.get_include_paths() == [
        Path("bld1/ABC/bla"),
        Path("bld1/IMPL/foo"),
    ]


def test_get_thirdparty_libs(tmp_path):
    third_party_dir = tmp_path / "ThirdParty"
    third_party_dir.mkdir()
    lib1 = third_party_dir / "lib1.a"
    lib1.touch()
    lib2 = third_party_dir / "subdir" / "lib2.lib"
    lib2.parent.mkdir()
    lib2.touch()

    assert LegacyBuildSystem(
        "", config=TransformerConfig(tmp_path, Path("X:/out"), "my/var")
    ).get_thirdparty_libs() == [Path("lib1.a"), Path("subdir/lib2.lib")]
