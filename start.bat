@echo off
cd /d "%~dp0"
echo Lancement de DofusTeam...
echo.

python main.py 2>nul
if errorlevel 1 (
    py main.py
    if errorlevel 1 (
        echo.
        echo ========================================
        echo   ERREUR — Details ci-dessus
        echo   Si tu vois une erreur rouge, note-la
        echo   et envoie-la pour qu'on corrige
        echo ========================================
        pause
    )
)
