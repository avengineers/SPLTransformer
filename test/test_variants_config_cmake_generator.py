import textwrap
from file_generators import VariantConfigCMakeGenerator


def test_to_string():
    generator = VariantConfigCMakeGenerator(
        compiler_flags="my_compiler_flags",
        linker_file="my/linker_file.lsl",
        link_flags="my_link_flags",
        cmake_toolchain_file="my/cmake_toolchain_file.cmake",
    )
    assert (
        textwrap.dedent(
            """\
        set(VARIANT_C_FLAGS my_compiler_flags)
        set(VARIANT_LINKER_FILE my/linker_file.lsl)
        set(VARIANT_LINK_FLAGS my_link_flags)
        set(CMAKE_TOOLCHAIN_FILE my/cmake_toolchain_file.cmake CACHE PATH "toolchain file")
        """
        )
        == generator.to_string()
    )
