"""DofusTeam — updater.py
Auto-update via GitHub Releases : vérifie/télécharge/applique une nouvelle
version, sans jamais bloquer l'UI (tout le réseau tourne en QThread, même
pattern que hunt.py).

Windows ne permet pas de remplacer un .exe en cours d'exécution. On télécharge
donc la nouvelle version sous un nom temporaire à côté de l'exe courant, puis
apply_update_and_restart() lance un petit .bat qui attend que l'exe se libère
(boucle de "del" tant que le fichier est verrouillé — il ne l'est plus une
fois ce process terminé), le remplace, relance l'appli et s'auto-supprime.
"""
import os, subprocess, sys
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal

try:
    import requests
    REQUESTS_OK = True
except ImportError:
    REQUESTS_OK = False

from paths import APP_DIR

REPO = "mayerjordan1/dofusteam-organizer"
API_LATEST = f"https://api.github.com/repos/{REPO}/releases/latest"
ASSET_NAME = "DofusTeam.exe"


def parse_version(v):
    """"V1.06" -> (1, 6). Tolérant : ignore tout ce qui n'est pas chiffre/point."""
    v = (v or "").strip().lstrip("Vv")
    parts = []
    for p in v.split("."):
        digits = "".join(c for c in p if c.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts) or (0,)


def is_newer(remote_tag, local_version):
    return parse_version(remote_tag) > parse_version(local_version)


def can_self_update():
    """True seulement en .exe compilé (PyInstaller frozen) — en dev (python
    main.py), il n'y a pas d'exe à remplacer, on ne fait que signaler."""
    return bool(getattr(sys, "frozen", False))


class UpdateCheckThread(QThread):
    """Émet (tag, download_url, size) si une version plus récente que
    current_version existe sur GitHub Releases, sinon ("", "", 0)."""
    done = pyqtSignal(str, str, int)

    def __init__(self, current_version):
        super().__init__()
        self.current_version = current_version

    def run(self):
        if not REQUESTS_OK:
            self.done.emit("", "", 0); return
        try:
            r = requests.get(API_LATEST, timeout=6,
                              headers={"Accept": "application/vnd.github+json"})
            r.raise_for_status()
            data = r.json()
            tag = data.get("tag_name", "")
            if not tag or not is_newer(tag, self.current_version):
                self.done.emit("", "", 0); return
            for asset in data.get("assets", []):
                if asset.get("name", "").lower() == ASSET_NAME.lower():
                    self.done.emit(tag, asset.get("browser_download_url", ""), asset.get("size", 0))
                    return
            self.done.emit("", "", 0)
        except Exception:
            self.done.emit("", "", 0)


class UpdateDownloadThread(QThread):
    """Télécharge l'asset vers dest_path (en streaming, avec un .part
    intermédiaire pour ne jamais laisser un fichier à moitié écrit sous le
    nom final)."""
    progress = pyqtSignal(int)
    done = pyqtSignal(bool, str)

    def __init__(self, url, dest_path):
        super().__init__()
        self.url = url
        self.dest_path = Path(dest_path)

    def run(self):
        tmp = self.dest_path.with_suffix(".part")
        try:
            r = requests.get(self.url, stream=True, timeout=15)
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            done = 0
            with open(tmp, "wb") as f:
                for chunk in r.iter_content(chunk_size=262144):
                    if not chunk:
                        continue
                    f.write(chunk)
                    done += len(chunk)
                    if total:
                        self.progress.emit(int(done * 100 / total))
            tmp.replace(self.dest_path)
            self.done.emit(True, "")
        except Exception as e:
            try: tmp.unlink(missing_ok=True)
            except Exception: pass
            self.done.emit(False, str(e))


def apply_update_and_restart(new_exe_path):
    """Écrit et lance le .bat de remplacement puis quitte immédiatement ce
    process (os._exit) pour libérer le verrou sur l'exe courant. Ne retourne
    jamais en cas de succès."""
    if not can_self_update():
        return False
    old_exe = Path(sys.executable)
    new_exe = Path(new_exe_path)
    bat_path = APP_DIR / "_dofusteam_update.bat"
    bat_content = (
        "@echo off\r\n"
        ":wait\r\n"
        f'del /f /q "{old_exe}" >nul 2>&1\r\n'
        f'if exist "{old_exe}" (\r\n'
        "    timeout /t 1 /nobreak >nul\r\n"
        "    goto wait\r\n"
        ")\r\n"
        f'ren "{new_exe}" "{old_exe.name}"\r\n'
        f'start "" "{old_exe}"\r\n'
        # Le nouvel exe (bootloader PyInstaller) vérifie au démarrage que son
        # processus parent (ce cmd.exe) est bien accessible — s'il se termine
        # trop vite après le "start" (non-bloquant), cette vérification échoue
        # avec "Security Validation failure: failed to obtain executable path
        # for parent process". On le garde vivant le temps que ça se stabilise.
        "timeout /t 2 /nobreak >nul\r\n"
        'del /f /q "%~f0"\r\n'
    )
    bat_path.write_text(bat_content, encoding="utf-8")
    subprocess.Popen(
        ["cmd", "/c", str(bat_path)],
        creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
        cwd=str(APP_DIR),
    )
    os._exit(0)
