@echo off
cd /d "%~dp0"
echo ========================================
echo   DofusTeam — Compilation en .exe
echo ========================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    py --version >nul 2>&1
    if errorlevel 1 (
        echo [ERREUR] Python introuvable.
        pause & exit /b 1
    )
    set PYTHON=py
) else (
    set PYTHON=python
)

:: Install PyInstaller if needed
echo Installation de PyInstaller...
%PYTHON% -m pip install pyinstaller --quiet

echo.
echo Compilation en cours... (1-2 minutes)
echo.

:: Build the exe
%PYTHON% -m PyInstaller ^
    --onefile ^
    --windowed ^
    --name "DofusTeam" ^
    --icon "skin\logo.ico" ^
    --add-data "skin;skin" ^
    --add-data "sounds;sounds" ^
    --add-data "settings.json;." ^
    --hidden-import "win32gui" ^
    --hidden-import "win32con" ^
    --hidden-import "win32api" ^
    --hidden-import "win32process" ^
    --hidden-import "keyboard" ^
    --hidden-import "mouse" ^
    --hidden-import "pyautogui" ^
    --hidden-import "PIL" ^
    --hidden-import "pygame" ^
    --hidden-import "tkinter" ^
    --hidden-import "requests" ^
    --hidden-import "pyperclip" ^
    main.py

if errorlevel 1 (
    echo.
    echo [ERREUR] La compilation a echoue.
    pause & exit /b 1
)

echo.
echo ========================================
echo   Succes ! DofusTeam.exe est dans dist\
echo   Copie les fichiers skin\ et sounds\
echo   dans le meme dossier que DofusTeam.exe
echo ========================================
echo.

:: Copy skin and sounds next to the exe
if exist "dist\DofusTeam.exe" (
    xcopy /E /I /Y "skin" "dist\skin" >nul
    xcopy /E /I /Y "sounds" "dist\sounds" >nul
    copy /Y "settings.json" "dist\settings.json" >nul
    echo [OK] Fichiers copies dans dist\
    echo Lancez dist\DofusTeam.exe directement !
)

pause
