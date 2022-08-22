# Readme

> **_NOTE:_** If you are running this script behind a proxy, make sure to set HTTP_PROXY, HTTPS_PROXY and NO_PROXY.
## Usage

> **_NOTE:_**  Although you can run the SPLTransformer project as a standalone tool, for convenience it is recommended to run it from within an SPL repository.

> **_NOTE:_**  To get a detailed explanation about how to transform a project from Make to CMake and import into a SPL, have a look into SPL repository README.md: https://github.com/avengineers/SPL/blob/develop/README.md

By running `build.bat --help` you will get a usage overview:

```
Usage:
  transformer.py --source=<source directory> --target=<target directory> --config=<config>
  transformer.py (-h | --help)

Options:
  -h --help        Show this screen.
  --source=DIR     Source directory holding a Dimensions make project
  --target=DIR     Target directory for the transformed CMake project
  --config=CONFIG  Config of the transformed CMake project (e.g., 'ANYAG_CoolProject')
  ```

  The following source structure is assumed (see /test/data/*)
  - IMPL/ directory in root
  - IMPL/Bld containing
    - makefile (can have multiple includes, not relevant. We use make to parse make)
    - Linker.ld (the linker command file)
  - IMPL/Src containing all source code files
  - Thirdparty/ directory in root that contains library files (currently only AnyAg directory is considered)

The source code directory will be copied as it is. This will be the base for the legacy source code directory.
The `makefile` must contain the following variables:
- PROJECT_ROOT: the root which contains a `Src` directory; project root dir is used to change relative paths for sources and inlcudes
- CC: compiler executable path
- LD: linker executable path
- AS: assembler executable path
- INCLUDE_PATH: list of all include directories
- SRC: list of all source code files to compile
- LDFILE: linker command file
- CCFLAGS: compiler flags
- ASMFLAGS: assembler flags
- TARGETFLAGS: generic flags for assembler and compiler
- LDFLAGS = linker flags
- PROJECTNAME: project name used for new variant naming

