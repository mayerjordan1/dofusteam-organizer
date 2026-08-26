"""Résolution centralisée des chemins (dev vs .exe PyInstaller onefile).

En onefile, sys.executable pointe vers l'exe réel (dossier où l'utilisateur
peut écrire settings.json), mais les assets embarqués via --add-data sont
extraits dans un dossier temporaire (sys._MEIPASS) à chaque lancement — ils
ne sont jamais physiquement à côté de l'exe. Toute lecture d'asset (skin,
sounds) doit donc passer par RES_DIR, pas par APP_DIR.
"""
import sys
from pathlib import Path

if getattr(sys, 'frozen', False):
    APP_DIR = Path(sys.executable).parent
    RES_DIR = Path(getattr(sys, '_MEIPASS', APP_DIR))
else:
    APP_DIR = Path(__file__).parent
    RES_DIR = APP_DIR

SKIN_DIR = RES_DIR / "skin"
SOUNDS_DIR = RES_DIR / "sounds"
SETTINGS_PATH = APP_DIR / "settings.json"
CACHE_DIR = APP_DIR / ".cache"
CACHE_DIR.mkdir(exist_ok=True)
