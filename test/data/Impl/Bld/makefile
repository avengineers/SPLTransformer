SCOOP_DIR = $(subst \,/,$(USERPROFILE))/scoop
ifdef SCOOP
	SCOOP_DIR = $(subst \,/,$(SCOOP))
endif
CC = $(SCOOP_DIR)/apps/gcc-llvm_11p2p0-13p0p0/11.2.0-13.0.0-9.0.0-r3/bin/gcc.exe
LD = $(SCOOP_DIR)/apps/gcc-llvm_11p2p0-13p0p0/11.2.0-13.0.0-9.0.0-r3/bin/gcc.exe
AS = $(SCOOP_DIR)/apps/gcc-llvm_11p2p0-13p0p0/11.2.0-13.0.0-9.0.0-r3/bin/gcc.exe

PROJECT_ROOT = ..

INCLUDE_PATH += $(PROJECT_ROOT)/Src/component_a
INCLUDE_PATH += $(PROJECT_ROOT)/Src/include_dir

SRC += $(PROJECT_ROOT)/Src/main.c
SRC += $(PROJECT_ROOT)/Src/../Src/component_a/component_a.c

LDFILE = Cfg/Linker.ld

CCFLAGS = -DKARSTEN \
		  -DMATTHIAS

TARGETFLAGS = -DALEXANDER

ASMFLAGS = -DFoo

PROJECTNAME = MY_PROJECT_NAME

BINDIR = ../Bin
LDFLAGS = -Dp=../Bin/blablub
