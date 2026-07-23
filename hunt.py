"""DofusTeam — hunt.py
Chasse au trésor : indices + zaap le plus proche via l'API DofusDB (lecture seule, aucun proxy).
"""
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

import time

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

from theme import STYLE, BG, BG2, BG3, ACC, RED, TEXT, MUT, BORDER

DIRECTIONS = [("Est", 0), ("Sud", 1), ("Ouest", 2), ("Nord", 3)]
API_HINTS = "https://api.dofusdb.fr/treasure-hunt"
API_ZAAP = "https://api.dofusdb.fr/transport-from-maps"


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
            self.done.emit({
                "name": (hint.get("name") or {}).get("fr", "Zaap"),
                "x": hint.get("x"), "y": hint.get("y"),
                "dist": e.get("distance"),
            }, "")
        except Exception as e:
            self.done.emit({}, str(e))


class HuntDialog(QDialog):
    def __init__(self, config=None, logic=None, parent=None):
        super().__init__(parent)
        self.config = config
        self.logic = logic
        self._hints = []
        self._search_thread = None
        self._zaap_thread = None
        self.setWindowTitle("🗺  Chasse au trésor")
        self.setFixedSize(440, 610)
        self.setStyleSheet(STYLE)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        hdr = QWidget()
        hdr.setStyleSheet("background:#151922;border-bottom:1px solid rgba(255,255,255,0.06);")
        hdr.setFixedHeight(50)
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(16, 0, 16, 0)
        title = QLabel("🗺  Chasse au trésor")
        title.setStyleSheet("font-size:15px;font-weight:700;")
        hl.addWidget(title)
        hl.addStretch()
        credit = QLabel("Données via DofusDB")
        credit.setStyleSheet("color:#9ca3af;font-size:10px;")
        hl.addWidget(credit)
        lay.addWidget(hdr)

        body = QWidget()
        bl = QVBoxLayout(body)
        bl.setContentsMargins(16, 12, 16, 12)
        bl.setSpacing(10)

        if not REQUESTS_OK:
            warn = QLabel("⚠️  Module 'requests' manquant.\nAjoute-le à requirements.txt et réinstalle les dépendances.")
            warn.setStyleSheet("color:#ff5c5c;font-size:11px;")
            warn.setWordWrap(True)
            bl.addWidget(warn)

        pos_row = QHBoxLayout()
        pos_row.addWidget(QLabel("Position actuelle :"))
        self.x_inp = QLineEdit()
        self.x_inp.setPlaceholderText("X")
        self.x_inp.setFixedWidth(60)
        pos_row.addWidget(self.x_inp)
        self.y_inp = QLineEdit()
        self.y_inp.setPlaceholderText("Y")
        self.y_inp.setFixedWidth(60)
        pos_row.addWidget(self.y_inp)
        pos_row.addStretch()
        bl.addLayout(pos_row)

        dir_row = QHBoxLayout()
        dir_row.addWidget(QLabel("Direction de l'indice :"))
        self.dir_c = QComboBox()
        for label, _ in DIRECTIONS:
            self.dir_c.addItem(label)
        dir_row.addWidget(self.dir_c)
        dir_row.addStretch()
        bl.addLayout(dir_row)

        self.search_btn = QPushButton("🔍  Chercher les indices")
        self.search_btn.setStyleSheet("background:#ff8a1e;color:#0f1115;border:none;border-radius:6px;padding:8px;font-weight:700;font-size:12px;")
        self.search_btn.clicked.connect(self._search)
        bl.addWidget(self.search_btn)

        self.status_lbl = QLabel("Entre ta position et lance la recherche.")
        self.status_lbl.setStyleSheet("color:#9ca3af;font-size:11px;")
        self.status_lbl.setWordWrap(True)
        bl.addWidget(self.status_lbl)

        self.results_list = QListWidget()
        self.results_list.itemClicked.connect(self._select_hint)
        bl.addWidget(self.results_list, 1)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background:rgba(255,255,255,0.07);")
        bl.addWidget(sep)

        self.zaap_box = QLabel("")
        self.zaap_box.setStyleSheet("background:#151922;border:1px solid rgba(255,255,255,0.07);border-radius:6px;padding:10px;font-size:12px;")
        self.zaap_box.setWordWrap(True)
        self.zaap_box.setMinimumHeight(60)
        bl.addWidget(self.zaap_box)

        self.copy_btn = QPushButton("📋  Copier la commande /travel")
        self.copy_btn.setStyleSheet("background:#c8a000;color:white;border:none;border-radius:6px;padding:8px;font-weight:700;font-size:12px;")
        self.copy_btn.setEnabled(False)
        self.copy_btn.clicked.connect(self._copy_travel)
        bl.addWidget(self.copy_btn)

        auto_row = QHBoxLayout()
        self.auto_chk = QCheckBox("Coller auto + valider dans le chat de :")
        self.auto_chk.setStyleSheet("font-size:11px;color:#9ca3af;")
        auto_row.addWidget(self.auto_chk)
        self.char_c = QComboBox()
        self.char_c.setFixedWidth(140)
        self._refresh_accounts()
        auto_row.addWidget(self.char_c)
        auto_row.addStretch()
        bl.addLayout(auto_row)

        can_auto = bool(self.config and self.logic and PYAUTOGUI_OK)
        self.auto_chk.setEnabled(can_auto)
        self.char_c.setEnabled(can_auto)
        if not can_auto:
            self.auto_chk.setText("Coller auto (indisponible — config/logic manquants)")

        lay.addWidget(body, 1)
        self._travel_cmd = None

    def _refresh_accounts(self):
        self.char_c.clear()
        if not self.logic: return
        for a in self.logic.all_accounts:
            self.char_c.addItem(a["name"], a["hwnd"])
        idx = getattr(self.logic, "_idx", 0)
        cycle = self.logic.get_cycle_list() if hasattr(self.logic, "get_cycle_list") else []
        if cycle and 0 <= idx < len(cycle):
            i = self.char_c.findData(cycle[idx]["hwnd"])
            if i >= 0:
                self.char_c.setCurrentIndex(i)

    def _search(self):
        if not REQUESTS_OK:
            return
        try:
            x = int(self.x_inp.text().strip())
            y = int(self.y_inp.text().strip())
        except ValueError:
            self.status_lbl.setText("⚠️  Coordonnées X/Y invalides.")
            self.status_lbl.setStyleSheet("color:#ff5c5c;font-size:11px;")
            return
        direction = DIRECTIONS[self.dir_c.currentIndex()][1]
        self.results_list.clear()
        self.zaap_box.setText("")
        self.copy_btn.setEnabled(False)
        self.search_btn.setEnabled(False)
        self.status_lbl.setText("Recherche en cours...")
        self.status_lbl.setStyleSheet("color:#9ca3af;font-size:11px;")
        self._search_thread = HintSearchThread(x, y, direction)
        self._search_thread.done.connect(self._on_hints)
        self._search_thread.start()

    def _on_hints(self, hints, error):
        self.search_btn.setEnabled(True)
        if error:
            self.status_lbl.setText(f"❌  Erreur : {error}")
            self.status_lbl.setStyleSheet("color:#ff5c5c;font-size:11px;")
            return
        self._hints = hints
        if not hints:
            self.status_lbl.setText("Aucun indice trouvé dans cette direction.")
            self.status_lbl.setStyleSheet("color:#9ca3af;font-size:11px;")
            return
        self.status_lbl.setText(f"{len(hints)} indice(s) trouvé(s) — sélectionne le tien.")
        self.status_lbl.setStyleSheet("color:#ff8a1e;font-size:11px;font-weight:600;")
        for h in hints:
            item = QListWidgetItem(f"{h['name']}   ·   {h['dist']} map(s)   ·   ({h['x']}, {h['y']})")
            item.setData(Qt.ItemDataRole.UserRole, h)
            self.results_list.addItem(item)

    def _select_hint(self, item):
        h = item.data(Qt.ItemDataRole.UserRole)
        if not h or not REQUESTS_OK:
            return
        self.zaap_box.setText("Recherche du zaap le plus proche...")
        self.copy_btn.setEnabled(False)
        self._zaap_thread = ZaapSearchThread(h["mapId"])
        self._zaap_thread.done.connect(lambda z, err, hh=h: self._on_zaap(hh, z, err))
        self._zaap_thread.start()

    def _on_zaap(self, hint, zaap, error):
        if error or not zaap:
            self.zaap_box.setText(f"⚠️  {error or 'Zaap introuvable.'}")
            self.copy_btn.setEnabled(False)
            self._travel_cmd = None
            return
        self._travel_cmd = f"/travel {zaap['x']},{zaap['y']}"
        self.zaap_box.setText(
            f"Zaap le plus proche : <b>{zaap['name']}</b> ({zaap['x']}, {zaap['y']}) — {zaap['dist']} map(s)\n"
            f"Commande : {self._travel_cmd}"
        )
        self.copy_btn.setEnabled(CLIPBOARD_OK)
        if self.auto_chk.isEnabled() and self.auto_chk.isChecked():
            self._auto_paste()

    def _copy_travel(self):
        if not self._travel_cmd or not CLIPBOARD_OK:
            return
        pyperclip.copy(self._travel_cmd)
        self.status_lbl.setText(f"✅  Copié : {self._travel_cmd}")
        self.status_lbl.setStyleSheet("color:#ff8a1e;font-size:11px;font-weight:600;")

    def _auto_paste(self):
        if not self._travel_cmd or not CLIPBOARD_OK or not PYAUTOGUI_OK or not self.logic or not self.config:
            return
        hwnd = self.char_c.currentData()
        if not hwnd:
            self.status_lbl.setText("⚠️  Aucun personnage sélectionné.")
            self.status_lbl.setStyleSheet("color:#ff5c5c;font-size:11px;")
            return
        cp = self.config.get("macro_positions", {}).get("chat_position")
        if not cp:
            self.status_lbl.setText("⚠️  Position du chat non calibrée (bouton CALIB CHAT).")
            self.status_lbl.setStyleSheet("color:#ff5c5c;font-size:11px;")
            return
        pyperclip.copy(self._travel_cmd)
        cmd = self._travel_cmd

        def _do():
            try:
                self.logic.focus_window(hwnd)
                time.sleep(0.2)
                pyautogui.click(cp[0], cp[1])
                time.sleep(0.15)
                pyautogui.hotkey("ctrl", "v")
                time.sleep(0.08)
                pyautogui.press("enter")
            except Exception as e:
                print(f"[hunt._auto_paste] {e}")

        import threading
        threading.Thread(target=_do, daemon=True).start()
        self.status_lbl.setText(f"✅  Collé automatiquement : {cmd}")
        self.status_lbl.setStyleSheet("color:#ff8a1e;font-size:11px;font-weight:600;")
