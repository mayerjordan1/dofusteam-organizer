# DofusTeam

Gestionnaire multi-compte pour Dofus Unity : switch instantané entre personnages, hotkeys globaux, macros Havre-sac/Zaap/Invite, menu radial, mini-toolbar flottante.

## Installation (Windows)

1. Télécharge la dernière release (`DofusTeam.exe`) dans l'onglet [Releases](../../releases), ou :
2. Lance `install.bat` (installe les dépendances Python) puis `start.bat`.

## Développement

```
pip install -r requirements.txt
python main.py
```

`settings.json` (ignoré par git) stocke ta configuration locale — comptes, ordre, calibration zaap. Un modèle vide est fourni dans `settings.example.json`.

## Build de l'exécutable

`build.bat` compile `main.py` en `DofusTeam.exe` via PyInstaller (Windows uniquement — utilise le workflow GitHub Actions pour builder depuis n'importe quel OS).

## Fonctionnalités

- Détection automatique des fenêtres Dofus Unity, switch de focus sans déclencher Alt+Tab.
- Hotkeys globaux configurables (next/prev/leader/refresh/tri de la barre des tâches).
- Menu radial (Alt + clic gauche) pour choisir un personnage au survol.
- Macros Havre-sac / Zaap / Invite avec délais aléatoires.
- Calibration par overlay pour adapter les macros à ta résolution d'écran.
- Presets d'ordre d'équipe, mini-toolbar flottante toujours au premier plan.

## Licence

MIT — voir [LICENSE](LICENSE).
