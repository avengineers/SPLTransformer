@echo on
set THIS_DIR=%~dp0

REM TODO: make this configurable
call %MAKESUPPORT_DIR%\set_cygwin_path.bat

@echo on
where make
make -s -f %THIS_DIR%collect.mak collect
