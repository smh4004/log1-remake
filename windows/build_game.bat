@echo off
setlocal
rem Builds the Legacy of Goku 1 remake from your own ROM dumps. Put this file in a folder with the four .gba dumps and double-click it.
rem Tools and working files go in C:\log1build, which you can delete afterwards. Nothing else on your PC changes.
title Legacy of Goku 1 remake build
set "ROMDIR=%~dp0"
set "WORK=C:\log1build"
set "BASH=%WORK%\msys64\usr\bin\bash.exe"
set "MSYSTEM=UCRT64"
set "CHERE_INVOKING=1"
set "MSYS2_PATH_TYPE=minimal"
if not exist "%WORK%" mkdir "%WORK%" || goto fail

if exist "%BASH%" goto tools
echo Downloading the build tools (MSYS2, about 100 MB)...
curl.exe -L --fail -o "%WORK%\msys2.sfx.exe" https://repo.msys2.org/distrib/msys2-x86_64-latest.sfx.exe || goto fail
"%WORK%\msys2.sfx.exe" -y -o"%WORK%" >nul || goto fail
del "%WORK%\msys2.sfx.exe"
"%BASH%" -lc "exit" >nul 2>&1

:tools
if exist "%WORK%\tools_ok" goto build
echo Installing compilers and Python. This takes a few minutes...
"%BASH%" -lc "pacman -Syu --noconfirm"
"%BASH%" -lc "pacman -Syu --noconfirm"
"%BASH%" -lc "pacman -S --noconfirm --needed git make mingw-w64-ucrt-x86_64-python mingw-w64-ucrt-x86_64-python-numpy mingw-w64-ucrt-x86_64-python-scipy mingw-w64-ucrt-x86_64-python-pillow mingw-w64-ucrt-x86_64-arm-none-eabi-gcc" || goto fail
echo ok> "%WORK%\tools_ok"

:build
cd /d "%WORK%" || goto fail
"%BASH%" -lc "set -o pipefail; { [ -d log1-remake/.git ] && git -C log1-remake pull --ff-only || git -c core.autocrlf=false clone https://github.com/smh4004/log1-remake; } && cd log1-remake && tools/build_all.sh \"$(cygpath -u \"$ROMDIR\")\" 2>&1 | tee ../build.log" || goto fail
copy /y "%WORK%\log1-remake\out\slice\slice.gba" "%ROMDIR%LegacyOfGoku1Remake.gba" >nul || goto fail
echo.
echo Finished. Your game is here: %ROMDIR%LegacyOfGoku1Remake.gba
echo You can delete C:\log1build if you won't rebuild it.
pause
exit /b 0

:fail
echo.
echo The build stopped. Send Claude the last lines above, or the file C:\log1build\build.log if it exists.
pause
exit /b 1
