from pathlib import Path
from LegacyBuildSystem import LegacyBuildSystem
from TransformerConfig import TransformerConfig


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
    make_var_dump = (
        "CPPFLAGS_INC_LIST = -I../COMMON/BLA/CompX -I../COMMON/BLU/CompY -IIMPL/foo"
    )
    input_dir = Path("X:/in")
    config = TransformerConfig(input_dir, Path("X:/out"), "my/var")
    config.build_dir_rel = "BLD"
    config.source_dir_rel = "BLD/IMPL"
    legacy_build = LegacyBuildSystem(make_var_dump, config)
    assert legacy_build.get_include_paths() == [
        Path("COMMON/BLA/CompX"),
        Path("COMMON/BLU/CompY"),
        Path("foo"),
    ]


def test_get_sources():
    make_var_dump = "VC_SRC_LIST = ../COMMON/file1.c IMPL/src/main.c"
    input_dir = Path("X:/in")
    config = TransformerConfig(input_dir, Path("X:/out"), "my/var")
    config.build_dir_rel = "BLD"
    config.source_dir_rel = "BLD/IMPL"
    legacy_build = LegacyBuildSystem(make_var_dump, config)
    assert legacy_build.get_source_paths() == [
        Path("COMMON/file1.c"),
        Path("src/main.c"),
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
