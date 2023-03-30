# this makefile (collect.mak) shall not have any influence on the included makefiles
# and therefore not be part of MAKEFILE_LIST.
undefine MAKEFILE_LIST

include Makefile

# store all global make variables created by legacy build env
$(file >$(MAKE_VARS_FILE),)
$(foreach v, \
      $(.VARIABLES), \
      $(file >>$(MAKE_VARS_FILE),$(v) = $($(v))) \
 )

.PHONY: collect

collect:
	@
