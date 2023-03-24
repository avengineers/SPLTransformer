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
"""
    make_dump = LegacyBuildSystem.parse_make_variables_dump(content)
    assert len(make_dump.keys()) == 4
    assert make_dump["MY_INCLUDES".lower()] == "-I../ABC/path -I../IMPL/path"


def test_search_include_paths():
    includes_str = "-I../ABC/path -I../IMPL/path"
    includes = LegacyBuildSystem.extract_include_paths(includes_str)
    assert includes == ["../ABC/path", "../IMPL/path"]


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
