@echo off
rmdir /S /Q build
rmdir /S /Q dist
pyinstaller compilar.spec
cd apife
c.bat
cd ..