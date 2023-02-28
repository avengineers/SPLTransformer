# this makefile (collect.mak) shall not have any influence on the included makefiles
# and therefore not be part of MAKEFILE_LIST.
undefine MAKEFILE_LIST

include makefile

# store all global make variables created by legacy build env
#MAKE_VARS_FILE := $(OUT_PATH)/variants/$(VARIANT)/original_make_vars.txt
#$(file >$(MAKE_VARS_FILE),)
#$(foreach v, \
#      $(.VARIABLES), \
#      $(file >>$(MAKE_VARS_FILE),$(v) = $($(v))) \
# )

# make a list's elements uniq
define uniq =
  $(eval seen :=)
  $(foreach _,$1,$(if $(filter $_,${seen}),,$(eval seen += $_)))
  ${seen}
endef


# parentheses can't be escaped
lp = (
rp = )
ccolon = C:

# We install Compilers via Scoop, so we need to replace the hardcoded paths from makefiles
# into the env var values from the Scoop packages
# Prerequisite: compiler package name in Scoop is equal to the compiler directory name inside the Dimensions repo
COMPILER_PARENT_DIR    := ../../ThirdParty/Compiler
COMPILER_DIR           := $(firstword $(subst /, ,$(subst $(COMPILER_PARENT_DIR),,$(CC))))
COMPILER_DIR_REL       := $(COMPILER_PARENT_DIR)/$(COMPILER_DIR)
COMPILER_DIR_ABS       := $(abspath $(COMPILER_DIR_REL))
COMPILER_PACKAGE       := $(subst $(ccolon),gcc,$(subst .,p,$(COMPILER_DIR)))

ifdef VC_SRC_LIST
sourcefiles            := $(subst ../src/,,$(subst ../Src/,,$(VC_SRC_LIST)))
else
sourcefiles            := $(subst $(abspath $(MQ_PROJECT_ROOT))/,,$(abspath $(SRC) $(ASM)))
endif
ifdef CPPFLAGS_INC_LIST
include_paths          := $(subst ../src/,,$(subst ../Src/,,$(subst -I,,$(CPPFLAGS_INC_LIST))))
else
include_paths          := $(subst $(COMPILER_DIR_ABS),$${COMPILER_PATH},$(subst $(abspath $(MQ_PROJECT_ROOT))/,,$(abspath $(INCLUDE_PATH))))
endif
# Currently we do not need this.
# include_paths          := $(call uniq,$(patsubst %/,%,$(dir $(sourcefiles)) $(include_paths)))

CMAKE_PARTS_FILE        := $(OUT_PATH)/variants/$(VARIANT)/parts.cmake
TOOLCHAIN_CMAKE_FILE    := $(OUT_PATH)/tools/toolchains/$(COMPILER_PACKAGE)/toolchain.cmake
CMAKE_VARIANT_FILE      := $(OUT_PATH)/variants/$(VARIANT)/config.cmake
CMAKE_LEGACY_FILE       := $(OUT_PATH)/legacy/$(VARIANT)/CMakeLists.txt
CMAKE_LEGACY_PARTS_FILE := $(OUT_PATH)/legacy/$(VARIANT)/parts.cmake

# Create CMakeLists.txt in legacy source
$(file  >$(CMAKE_LEGACY_FILE),# Generated by Transformer)
$(file >>$(CMAKE_LEGACY_FILE),include(parts.cmake))
$(file >>$(CMAKE_LEGACY_FILE),spl_create_component())

# Create parts.cmake of legacy source component
$(file  >$(CMAKE_LEGACY_PARTS_FILE),# Generated by Transformer)
$(foreach sourcefile,$(sourcefiles),$(file >>$(CMAKE_LEGACY_PARTS_FILE),spl_add_source($(patsubst Src/%,%,$(sourcefile)))))

# Create variant.cmake
$(file  >$(CMAKE_VARIANT_FILE),# Generated by Transformer)
ifneq (,$(findstring TriCore_v6,$(COMPILER_PACKAGE)))
$(file >>$(CMAKE_VARIANT_FILE),set(VARIANT_LINKER_FILE $${CMAKE_CURRENT_LIST_DIR}/Bld/$(LDFILE)))
endif
$(file >>$(CMAKE_VARIANT_FILE),set(CMAKE_TOOLCHAIN_FILE tools/toolchains/$(COMPILER_PACKAGE)/toolchain.cmake CACHE PATH "toolchain file"))

# Create parts.cmake of variant
$(file  >$(CMAKE_PARTS_FILE),# Generated by Transformer)
$(foreach include_path,$(include_paths),$(file >>$(CMAKE_PARTS_FILE),spl_add_include(/legacy/$(VARIANT)/$(patsubst Src/%,%,$(include_path)))))
$(file  >>$(CMAKE_PARTS_FILE),)
$(file >>$(CMAKE_PARTS_FILE),spl_add_component(legacy/$(VARIANT)))
ifneq (,$(strip $(LDFILE)))
ifneq (,$(findstring comp_20,$(COMPILER_PACKAGE)))
$(file >>$(CMAKE_PARTS_FILE),target_link_libraries($${LINK_TARGET_NAME} $${CMAKE_CURRENT_LIST_DIR}/Bld/$(LDFILE)))
endif
endif

# Create toolchain.cmake
$(file  >$(TOOLCHAIN_CMAKE_FILE),# Generated by Transformer)
ifneq (,$(findstring $(COMPILER_DIR_ABS),$(abspath $(CC))))
$(file >>$(TOOLCHAIN_CMAKE_FILE),string(REPLACE "\\" "/" COMPILER_PATH $$ENV{$(COMPILER_PACKAGE)_ROOT}))
endif
$(file >>$(TOOLCHAIN_CMAKE_FILE),set(CMAKE_C_COMPILER "$(subst $(COMPILER_DIR_ABS),$${COMPILER_PATH},$(abspath $(CC)))"))
$(file >>$(TOOLCHAIN_CMAKE_FILE),set(CMAKE_CXX_COMPILER $${CMAKE_C_COMPILER}))
$(file >>$(TOOLCHAIN_CMAKE_FILE),set(CMAKE_ASM_COMPILER "$(subst $(COMPILER_DIR_ABS),$${COMPILER_PATH},$(abspath $(AS)))"))
ifneq (,$(findstring comp_20,$(COMPILER_PACKAGE)))
CCFLAGS := $(subst -nofloatio,,$(CCFLAGS))
$(file >>$(TOOLCHAIN_CMAKE_FILE),set(CMAKE_DEPFILE_FLAGS_C --make_depends))
$(file >>$(TOOLCHAIN_CMAKE_FILE),set(CMAKE_DEPFILE_FLAGS_ASM --make_depends))
endif
ifneq (,$(findstring TriCore_v6,$(COMPILER_PACKAGE)))
$(file >>$(TOOLCHAIN_CMAKE_FILE),set(CMAKE_DEPFILE_FLAGS_C "--dep-file=<DEP_FILE>"))
$(file >>$(TOOLCHAIN_CMAKE_FILE),set(CMAKE_DEPFILE_FLAGS_ASM "--dep-file=<DEP_FILE>"))
endif
# Internal hidden CMake feature that forces dependency file names with pattern <sourcefile>.d, e.g., main.c.d
# We need this because Greenhills compiler creates dependencies file with --make_depends and implicite file name.
# GCC has no problem with this setting because the name of dependency file is explicitely given
$(file >>$(TOOLCHAIN_CMAKE_FILE),set(CMAKE_C_DEPFILE_EXTENSION_REPLACE 1))
$(file >>$(TOOLCHAIN_CMAKE_FILE),set(CMAKE_ASM_DEPFILE_EXTENSION_REPLACE 1))

ifneq (,$(findstring TriCore_v6,$(COMPILER_PACKAGE)))
$(file >>$(TOOLCHAIN_CMAKE_FILE),set(CMAKE_C_RESPONSE_FILE_LINK_FLAG "-f "))
endif

ifneq (,$(strip $(TARGETFLAGS)))
CCFLAGS := $(CCFLAGS) $(TARGETFLAGS)
ASMFLAGS := $(ASMFLAGS) $(TARGETFLAGS)
endif

$(file >>$(TOOLCHAIN_CMAKE_FILE),)
ifdef CCFLAGS
$(file >>$(TOOLCHAIN_CMAKE_FILE),set(COMPILE_C_FLAGS $(subst -list_dir=../Bld/Lst,,$(CCFLAGS))))
endif
ifdef CFLAGS
$(file >>$(TOOLCHAIN_CMAKE_FILE),set(COMPILE_C_FLAGS $(subst -list_dir=../Bld/Lst,,$(CFLAGS))))
endif
ifdef ASMFLAGS
$(file >>$(TOOLCHAIN_CMAKE_FILE),set(COMPILE_ASM_FLAGS $(ASMFLAGS)))
endif
ifdef ASFLAGS
$(file >>$(TOOLCHAIN_CMAKE_FILE),set(COMPILE_ASM_FLAGS $(ASFLAGS)))
endif
$(file >>$(TOOLCHAIN_CMAKE_FILE),add_compile_options$(lp))
$(file >>$(TOOLCHAIN_CMAKE_FILE),    "$$<$$<COMPILE_LANGUAGE:C>:$${COMPILE_C_FLAGS}>")
$(file >>$(TOOLCHAIN_CMAKE_FILE),    "$$<$$<COMPILE_LANGUAGE:ASM>:$${COMPILE_ASM_FLAGS}>")
$(file >>$(TOOLCHAIN_CMAKE_FILE),$(rp))

ifeq ($(COMPILER_PACKAGE),TriCore_v6p2r2p2)
LDFLAGS := $(LDFLAGS) -lcs_fpu -lfp_fpu -lrt
endif

$(file >>$(TOOLCHAIN_CMAKE_FILE),add_link_options($(subst $(PROJECTNAME),$${FLAVOR}_$${SUBSYSTEM},$(subst $(BINDIR),.,$(subst $(COMPILER_DIR_REL),$${COMPILER_PATH},$(LDFLAGS))))))
ifneq (,$(findstring TriCore_v6,$(COMPILER_PACKAGE)))
$(file >>$(TOOLCHAIN_CMAKE_FILE),if (VARIANT_LINKER_FILE))
$(file >>$(TOOLCHAIN_CMAKE_FILE),    add_link_options(--lsl-file=$${VARIANT_LINKER_FILE}))
$(file >>$(TOOLCHAIN_CMAKE_FILE),else())
$(file >>$(TOOLCHAIN_CMAKE_FILE),    add_link_options(--lsl-file=$${CMAKE_CURRENT_LIST_DIR}/check.lsl))
$(file >>$(TOOLCHAIN_CMAKE_FILE),endif())
endif

ifneq (,$(findstring TriCore_v6,$(COMPILER_PACKAGE)))
$(file >>$(TOOLCHAIN_CMAKE_FILE),set(CMAKE_C_LINK_EXECUTABLE "$${COMPILER_PATH}/ctc/bin/ltc.exe -o <TARGET> <OBJECTS> <LINK_FLAGS>"))
endif

.PHONY: collect

collect:
	@