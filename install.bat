@echo off
cd /d "%~dp0"
echo ========================================
echo   DofusTeam — Installation
echo ========================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    py --version >nul 2>&1
    if errorlevel 1 ( echo [ERREUR] Python introuvable. & pause & exit /b 1 )
    set PYTHON=py
) else ( set PYTHON=python )

echo [OK] Python detecte
echo.
echo Installation des dependances...
echo.
%PYTHON% -m pip install --upgrade pip setuptools wheel --quiet
%PYTHON% -m pip install PyQt6
%PYTHON% -m pip install pywin32
%PYTHON% -m pip install keyboard
%PYTHON% -m pip install mouse
%PYTHON% -m pip install pyautogui
%PYTHON% -m pip install pyperclip
%PYTHON% -m pip install Pillow
%PYTHON% -m pip install pygame --quiet 2>nul || echo [INFO] pygame optionnel - non installe, sons desactives

echo.
echo ========================================
echo   Termine ! Lancez start.bat
echo ========================================
pause
