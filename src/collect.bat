@echo on
set THIS_DIR=%~dp0

set INPUT_PATH=%1
set OUT_PATH=%2
set BUILD_DIR_REL=%3
set VARIANT=%4

pushd %INPUT_PATH%\%BUILD_DIR_REL%

REM TODO: make this configurable
set MAKESUPPORT_DIR=%INPUT_PATH%\COMMON\CBD\MakeSupport
call %MAKESUPPORT_DIR%\set_cygwin_path.bat

@echo on
where make
make -s -f %THIS_DIR%collect.mak collect

popd
