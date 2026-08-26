"""
DofusTeam — zaap_favorites.py
Gestion des zaap favoris + macro auto-zaap vers destination
"""
import time, threading, random, unicodedata
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

try:
    import pyautogui, pyperclip
    pyautogui.FAILSAFE=False
    MACRO_OK=True
except ImportError:
    MACRO_OK=False

try:
    import win32gui, win32api, win32con
    WINDOWS=True
except ImportError:
    WINDOWS=False

from paths import SKIN_DIR
from theme import BG, BG2, BG3, ACC, TEXT, MUT, GOLD, RED, STYLE


def _norm(s):
    """Retire les accents ("â" -> "a") pour une recherche insensible aux accents."""
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").lower()


def run_zaap_to_destination(config, logic, destination_name, on_status=None):
    """
    Full auto-zaap macro to a specific destination:
    1. H on all windows (open havre-sacs)
    2. Click calibrated zaap on all windows
    3. Paste destination on all windows + Enter
    """
    if not MACRO_OK:
        if on_status: on_status("❌ pyautogui manquant")
        return

    def _run():
        accounts  = logic.get_cycle_list()
        if not accounts:
            if on_status: on_status("⚠ Aucun compte actif"); return

        zaaps      = config.get("macro_positions", {}).get("zaaps", {})
        haven_key  = config.get("game_haven_key", "h")
        open_delay = float(config.get("zaap_open_delay", 1.0))

        try: import ctypes; ctypes.windll.user32.BlockInput(True)
        except: pass

        # Phase 1: H rapide sur chaque fenetre (comme la main)
        if on_status: on_status(f"Phase 1 — Ouverture havresacs → {destination_name}")
        for acc in accounts:
            hwnd = acc["hwnd"]
            logic.focus_window(hwnd)
            for _ in range(15):
                try:
                    if win32gui.GetForegroundWindow() == hwnd: break
                except: pass
                time.sleep(0.1)
            time.sleep(0.08)
            try:
                import keyboard as _kb; _kb.send(haven_key)
            except:
                try:
                    vk = ord(haven_key.upper())
                    win32api.keybd_event(vk, 0, 0, 0); time.sleep(0.05)
                    win32api.keybd_event(vk, 0, 0x0002, 0)
                except: pyautogui.press(haven_key)
            time.sleep(0.12)

        if on_status: on_status(f"⏳ Chargement havresacs... ({open_delay}s)")
        time.sleep(open_delay)

        # Phase 2: Click zaap on all windows
        if on_status: on_status("⚡ Clic zaaps...")
        for acc in accounts:
            name = acc["name"]; hwnd = acc["hwnd"]
            if name not in zaaps: continue
            logic.focus_window(hwnd)
            for _ in range(15):
                try:
                    if win32gui.GetForegroundWindow() == hwnd: break
                except: pass
                time.sleep(0.1)
            time.sleep(0.1)
            try:
                rect = win32gui.GetWindowRect(hwnd)
                w = rect[2]-rect[0]; h = rect[3]-rect[1]
                rx,ry = zaaps[name]
                pyautogui.click(int(rect[0]+w*rx), int(rect[1]+h*ry))
            except Exception as e:
                if on_status: on_status(f"⚠ Zaap clic {name}: {e}")
            time.sleep(0.25)

        time.sleep(0.5)

        # Phase 3: Paste destination on all windows + Enter
        if on_status: on_status(f"📋 Destination: {destination_name}")
        pyperclip.copy(destination_name)

        for i, acc in enumerate(accounts):
            hwnd = acc["hwnd"]
            logic.focus_window(hwnd)
            for _ in range(15):
                try:
                    if win32gui.GetForegroundWindow() == hwnd: break
                except: pass
                time.sleep(0.08)
            time.sleep(0.08)
            pyautogui.hotkey("ctrl", "a")
            time.sleep(0.04)
            pyautogui.hotkey("ctrl", "v")
            time.sleep(0.15)
            pyautogui.press("enter")
            time.sleep(random.uniform(0.1, 0.18))

        try: import ctypes; ctypes.windll.user32.BlockInput(False)
        except: pass
        if on_status: on_status(f"✅ Tous zaapés → {destination_name} !")

    threading.Thread(target=_run, daemon=True).start()


class ZaapFavoritesDialog(QDialog):
    """Fenêtre de gestion des zaap favoris."""

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("⚡ Zaap Favoris")
        self.setFixedSize(560, 580)
        self.setStyleSheet(STYLE)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(0,0,0,0)

        # Header
        hdr = QWidget(); hdr.setObjectName("FavHeader")
        hdr.setStyleSheet(f"QWidget#FavHeader{{background:{BG2};border-bottom:1px solid rgba(255,255,255,0.06);}}"); hdr.setFixedHeight(52)
        hl = QHBoxLayout(hdr); hl.setContentsMargins(16,0,16,0)
        title = QLabel("⚡  Zaap Favoris")
        title.setStyleSheet(f"font-size:15px;font-weight:700;font-family:'Space Mono';color:{TEXT};")
        hl.addWidget(title); hl.addStretch()
        info = QLabel("☆ = marquer comme favori")
        info.setStyleSheet(f"color:{MUT};font-size:11px;"); hl.addWidget(info)
        lay.addWidget(hdr)

        content = QWidget(); cl = QVBoxLayout(content); cl.setContentsMargins(12,10,12,12); cl.setSpacing(8)

        # Search
        search_row = QHBoxLayout(); search_row.setSpacing(6)
        self.search = QLineEdit(); self.search.setPlaceholderText("🔍 Rechercher un territoire...")
        self.search.textChanged.connect(self._filter); search_row.addWidget(self.search)
        self.clear_search = QPushButton("✕"); self.clear_search.setFixedSize(26,26)
        self.clear_search.setToolTip("Effacer la recherche")
        self.clear_search.setStyleSheet(f"background:{BG3};color:{MUT};border:1px solid rgba(255,255,255,0.07);border-radius:6px;font-size:11px;")
        self.clear_search.clicked.connect(self.search.clear); search_row.addWidget(self.clear_search)
        cl.addLayout(search_row)

        # Tabs: Favoris / Tous
        tab_row = QHBoxLayout()
        self.tab_favs = QPushButton("★ Favoris"); self.tab_all = QPushButton("Tous (42)")
        for b in (self.tab_favs, self.tab_all):
            b.setStyleSheet(f"background:{BG3};border:1px solid rgba(255,255,255,0.07);border-radius:6px;padding:5px 16px;")
        self.tab_favs.clicked.connect(lambda: self._show_tab("favs"))
        self.tab_all.clicked.connect(lambda: self._show_tab("all"))
        tab_row.addWidget(self.tab_favs); tab_row.addWidget(self.tab_all); tab_row.addStretch()
        cl.addLayout(tab_row)

        # List
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        self.list_w = QWidget(); self.list_l = QVBoxLayout(self.list_w)
        self.list_l.setSpacing(2); self.list_l.setContentsMargins(0,0,0,0)
        self.list_l.addStretch(); scroll.setWidget(self.list_w); cl.addWidget(scroll)

        lay.addWidget(content)
        self._current_tab = "favs"
        self._show_tab("favs")

    def _show_tab(self, tab):
        self._current_tab = tab
        self.tab_favs.setStyleSheet(
            f"background:rgba(255,138,30,0.12);color:{ACC};border:1px solid rgba(255,138,30,0.3);border-radius:6px;padding:5px 16px;font-weight:700;"
            if tab=="favs" else
            f"background:{BG3};border:1px solid rgba(255,255,255,0.07);border-radius:6px;padding:5px 16px;"
        )
        self.tab_all.setStyleSheet(
            f"background:rgba(255,138,30,0.12);color:{ACC};border:1px solid rgba(255,138,30,0.3);border-radius:6px;padding:5px 16px;font-weight:700;"
            if tab=="all" else
            f"background:{BG3};border:1px solid rgba(255,255,255,0.07);border-radius:6px;padding:5px 16px;"
        )
        self._filter()

    def _filter(self):
        from zaap_data import ZAAPS, get_favorites
        query = _norm(self.search.text())
        favs  = get_favorites(self.config)

        if self._current_tab == "favs":
            items = [z for z in ZAAPS if z["name"] in favs]
        else:
            items = ZAAPS

        if query:
            items = [z for z in items if query in _norm(z["name"]) or query in _norm(z["region"])]

        # Rebuild list
        while self.list_l.count() > 1:
            item = self.list_l.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        for z in items:
            self._add_row(z, z["name"] in favs)

    def _add_row(self, z, is_fav):
        from zaap_data import toggle_favorite
        row = QWidget(); row.setObjectName(f"FavRow{id(z)}")
        row.setStyleSheet(f"QWidget#FavRow{id(z)}{{background:{BG2};border-radius:6px;}}")
        rl = QHBoxLayout(row); rl.setContentsMargins(10,6,10,6); rl.setSpacing(10)

        # Star toggle
        star = QPushButton("★" if is_fav else "☆"); star.setFixedSize(36,28)
        fav_style = f"background:rgba(200,160,0,0.15);color:{GOLD};border:1px solid rgba(200,160,0,0.3);border-radius:5px;font-family:'Segoe UI Symbol','Arial Unicode MS';font-size:15px;"
        nfv_style = f"background:transparent;color:{MUT};border:none;border-radius:5px;font-family:'Segoe UI Symbol','Arial Unicode MS';font-size:15px;"
        star.setStyleSheet(fav_style if is_fav else nfv_style)
        star.clicked.connect(lambda: (toggle_favorite(self.config, z["name"]), self._filter()))
        rl.addWidget(star)

        # Name + region
        name_lbl = QLabel(z["name"]); name_lbl.setStyleSheet(f"font-weight:600;color:{TEXT};font-size:12px;"); name_lbl.setMinimumWidth(200)
        reg_lbl  = QLabel(z["region"]); reg_lbl.setStyleSheet(f"color:{MUT};font-size:11px;"); reg_lbl.setMinimumWidth(150)
        coord_lbl = QLabel(f"[{z['coords'][0]},{z['coords'][1]}]"); coord_lbl.setStyleSheet(f"color:{ACC};font-size:10px;font-family:'Space Mono';")
        rl.addWidget(name_lbl); rl.addWidget(reg_lbl); rl.addWidget(coord_lbl); rl.addStretch()

        self.list_l.insertWidget(self.list_l.count()-1, row)
