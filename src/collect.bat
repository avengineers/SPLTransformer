@echo off
set THIS_DIR=%~dp0

set BUILD_IN_PATH=%1
set OUT_PATH=%2
set VARIANT=%3

pushd %BUILD_IN_PATH%
make -s -f %THIS_DIR%collect.mak collect
popd
