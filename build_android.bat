@echo off
chcp 437 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set VSLANG=1033

call "E:\VS2022BuildTools\VC\Auxiliary\Build\vcvars64.bat"
if errorlevel 1 (
    echo Failed to setup VS environment
    exit /b 1
)

cd /d E:\frida-16.4.7

echo Configuring Frida for android-arm64...
python -c "import sys; sys.path.insert(0, '.'); from releng.meson_configure import main; sys.argv = ['configure', '.', '--host', 'android-arm64']; main()"
if errorlevel 1 (
    echo Configuration failed
    exit /b 1
)

echo Building...
python -c "import sys; sys.path.insert(0, '.'); from releng.meson_make import main; sys.argv = ['make', '.', './build', 'all']; main()"

echo Done!
