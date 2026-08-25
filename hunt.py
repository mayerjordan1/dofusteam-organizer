"""DofusTeam — hunt.py
Chasse au trésor : indices + zaap le plus proche via l'API DofusDB (lecture seule, aucun proxy).
Logique réseau réutilisée par pages/chasse_tresor.py (page embarquée dans l'appli).
"""
from PyQt6.QtCore import QThread, pyqtSignal

try:
    import requests
    REQUESTS_OK = True
except ImportError:
    REQUESTS_OK = False
try:
    import pyperclip
    CLIPBOARD_OK = True
except ImportError:
    CLIPBOARD_OK = False
try:
    import pyautogui
    pyautogui.FAILSAFE = False
    PYAUTOGUI_OK = True
except ImportError:
    PYAUTOGUI_OK = False

DIRECTIONS = [("Est", 0), ("Sud", 1), ("Ouest", 2), ("Nord", 3)]
API_HINTS = "https://api.dofusdb.fr/treasure-hunt"
API_ZAAP = "https://api.dofusdb.fr/transport-from-maps"
API_SUBAREA = "https://api.dofusdb.fr/subareas"


class HintSearchThread(QThread):
    done = pyqtSignal(list, str)

    def __init__(self, x, y, direction):
        super().__init__()
        self.x = x
        self.y = y
        self.direction = direction

    def run(self):
        try:
            r = requests.get(API_HINTS, params={
                "x": self.x, "y": self.y, "direction": self.direction,
                "$limit": 50, "lang": "fr",
            }, timeout=8)
            r.raise_for_status()
            data = r.json()
            hints = []
            for m in data.get("data", []):
                for poi in (m.get("pois") or []):
                    hints.append({
                        "mapId": m.get("id"), "x": m.get("posX"), "y": m.get("posY"),
                        "dist": m.get("distance", 0),
                        "name": (poi.get("name") or {}).get("fr", f"Indice #{poi.get('id')}"),
                    })
            hints.sort(key=lambda h: h["dist"])
            self.done.emit(hints, "")
        except Exception as e:
            self.done.emit([], str(e))


class ZaapSearchThread(QThread):
    done = pyqtSignal(dict, str)

    def __init__(self, map_id):
        super().__init__()
        self.map_id = map_id

    def run(self):
        try:
            r = requests.get(API_ZAAP, params={
                "id": self.map_id, "$sort": "distance", "$limit": 1, "lang": "fr",
            }, timeout=8)
            r.raise_for_status()
            entries = r.json().get("data", [])
            if not entries:
                self.done.emit({}, "Aucun zaap trouvé pour cette map.")
                return
            e = entries[0]
            hint = e.get("hint") or {}
            # Le nom du "hint" est toujours générique ("Zaap") : c'est un type de
            # point d'intérêt, pas un lieu. Le vrai nom du zaap (ex: "Cité d'Astrub")
            # vient de la sous-zone (subareaId) de la map où il se trouve.
            name = "Zaap"
            subarea_id = hint.get("subareaId")
            if subarea_id:
                try:
                    rs = requests.get(f"{API_SUBAREA}/{subarea_id}", params={"lang": "fr"}, timeout=8)
                    rs.raise_for_status()
                    subarea_name = (rs.json().get("name") or {}).get("fr")
                    if subarea_name:
                        name = f"Zaap — {subarea_name}"
                except Exception:
                    pass
            self.done.emit({
                "name": name,
                "x": hint.get("x"), "y": hint.get("y"),
                "dist": e.get("distance"),
            }, "")
        except Exception as e:
            self.done.emit({}, str(e))
