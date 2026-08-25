"""Page "Chasse au trésor" — résolution d'indices embarquée (DofusDB).

Anciennement un simple lanceur qui ouvrait HuntDialog en modal (hunt.py) ;
la logique réseau (HintSearchThread/ZaapSearchThread, appels DofusDB) reste
dans hunt.py et est réutilisée ici telle quelle — seule l'UI est reprise en
page intégrée (theme.py partagé) pour rester cohérente avec le reste de
l'appli (Mes équipes, Fenêtres & scan, ...).
"""
import threading
import time

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QListWidget, QListWidgetItem, QCheckBox, QFrame,
)
from PyQt6.QtCore import Qt, QSize

from theme import (TEXT, MUT, BG2, BG3, BORDER, ACC, GOLD, section_label,
                    glass_card, accent_btn, ghost_btn, load_icon, mono)
from hunt import (DIRECTIONS, HintSearchThread, ZaapSearchThread,
                   REQUESTS_OK, CLIPBOARD_OK, PYAUTOGUI_OK)

# Flèche + position dans la grille 3x3 (compas) pour chaque direction DofusDB
_DIR_ARROWS = {0: ("→", 1, 2), 1: ("↓", 2, 1), 2: ("←", 1, 0), 3: ("↑", 0, 1)}


def _make_header(title, subtitle):
    header = QWidget()
    header.setObjectName("PageHeader")
    lay = QVBoxLayout(header)
    lay.setContentsMargins(24, 18, 24, 14)
    lay.setSpacing(2)
    t = QLabel(title)
    t.setObjectName("PageTitle")
    lay.addWidget(t)
    if subtitle:
        s = QLabel(subtitle)
        s.setObjectName("PageSubtitle")
        lay.addWidget(s)
    return header


class ChasseTresorPage(QWidget):
    """Recherche d'indices (position + direction) à gauche, résultat du zaap
    le plus proche + collage auto à droite — même découpage deux-colonnes
    que Mes équipes (contenu principal / panneau d'actions à largeur fixe)."""

    def __init__(self, config, logic, parent=None):
        super().__init__(parent)
        self.config = config
        self.logic = logic
        self._hints = []
        self._travel_cmd = None
        self._search_thread = None
        self._zaap_thread = None
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        lay.addWidget(_make_header(
            "Chasse au trésor",
            "Résolution d'indices et recherche de zaaps via DofusDB.",
        ))

        body = QWidget()
        body_lay = QHBoxLayout(body)
        body_lay.setContentsMargins(24, 18, 24, 18)
        body_lay.setSpacing(16)

        body_lay.addWidget(self._search_card(), 1)
        body_lay.addWidget(self._result_card())

        lay.addWidget(body, 1)

    def _search_card(self):
        c = glass_card(QWidget())
        clay = QVBoxLayout(c)
        clay.setContentsMargins(16, 14, 16, 14)
        clay.setSpacing(10)

        clay.addWidget(section_label("🔍 Recherche d'indice"))

        if not REQUESTS_OK:
            warn = QLabel("⚠️  Module 'requests' manquant.\nAjoute-le à requirements.txt et réinstalle les dépendances.")
            warn.setStyleSheet("color:#ff5c5c; font-size:11px; background:transparent;")
            warn.setWordWrap(True)
            clay.addWidget(warn)

        pos_row = QHBoxLayout()
        pos_row.setSpacing(8)
        pos_lbl = QLabel("Position actuelle :")
        pos_lbl.setStyleSheet(f"color:{TEXT}; font-size:12px; background:transparent;")
        pos_row.addWidget(pos_lbl)
        self.x_inp = QLineEdit(); self.x_inp.setPlaceholderText("X"); self.x_inp.setFixedWidth(60)
        pos_row.addWidget(self.x_inp)
        self.y_inp = QLineEdit(); self.y_inp.setPlaceholderText("Y"); self.y_inp.setFixedWidth(60)
        pos_row.addWidget(self.y_inp)
        pos_row.addStretch()
        clay.addLayout(pos_row)

        dir_lbl = QLabel("Direction de l'indice :")
        dir_lbl.setStyleSheet(f"color:{TEXT}; font-size:12px; background:transparent;")
        clay.addWidget(dir_lbl)
        self.direction = DIRECTIONS[0][1]
        clay.addWidget(self._dir_pad())

        self.search_btn = accent_btn("🔍  Chercher les indices", self._search)
        clay.addWidget(self.search_btn)

        self.status_lbl = QLabel("Entre ta position et lance la recherche.")
        self.status_lbl.setStyleSheet(f"color:{MUT}; font-size:11px; background:transparent;")
        self.status_lbl.setWordWrap(True)
        clay.addWidget(self.status_lbl)

        self.results_list = QListWidget()
        self.results_list.itemClicked.connect(self._select_hint)
        clay.addWidget(self.results_list, 1)

        return c

    def _dir_pad(self):
        """Pavé façon boussole (3x3) : une flèche cliquable par direction DofusDB,
        au lieu d'un menu déroulant texte (Est/Sud/Ouest/Nord) — plus rapide à lire."""
        pad = QWidget()
        pad.setStyleSheet("background:transparent;")
        grid = QGridLayout(pad)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(4)

        self._dir_btns = {}
        for idx, (arrow, row, col) in _DIR_ARROWS.items():
            b = QPushButton(arrow)
            b.setCheckable(True)
            b.setFixedSize(34, 34)
            b.setStyleSheet(
                f"QPushButton{{background:{BG3};color:{TEXT};border:1px solid {BORDER};"
                f"border-radius:8px;font-size:16px;font-weight:700;}}"
                f"QPushButton:checked{{background:{ACC};color:#0f1115;border-color:{ACC};}}"
                f"QPushButton:hover{{border-color:{ACC};}}"
            )
            b.clicked.connect(lambda _, i=idx: self._set_direction(i))
            grid.addWidget(b, row, col, alignment=Qt.AlignmentFlag.AlignCenter)
            self._dir_btns[idx] = b

        self._dir_btns[self.direction].setChecked(True)

        wrap = QHBoxLayout()
        wrap.addWidget(pad)
        wrap.addStretch()
        wrap_w = QWidget()
        wrap_w.setStyleSheet("background:transparent;")
        wrap_w.setLayout(wrap)
        return wrap_w

    def _set_direction(self, idx):
        self.direction = idx
        for i, b in self._dir_btns.items():
            b.setChecked(i == idx)

    def _result_card(self):
        c = glass_card(QWidget())
        c.setFixedWidth(280)
        clay = QVBoxLayout(c)
        clay.setContentsMargins(16, 14, 16, 14)
        clay.setSpacing(10)

        clay.addWidget(section_label("🧭 Zaap le plus proche"))

        box = QWidget()
        box.setObjectName("ZaapBox")
        box.setStyleSheet(f"QWidget#ZaapBox{{background:{BG2}; border:1px solid {BORDER}; border-radius:8px;}}")
        box_lay = QVBoxLayout(box)
        box_lay.setContentsMargins(12, 12, 12, 12)
        box_lay.setSpacing(8)

        self.zaap_placeholder = QLabel("Sélectionne un indice à gauche\npour voir le zaap le plus proche.")
        self.zaap_placeholder.setStyleSheet(f"font-size:12px; color:{MUT}; background:transparent;")
        self.zaap_placeholder.setWordWrap(True)
        box_lay.addWidget(self.zaap_placeholder)

        self.zaap_result = QWidget()
        self.zaap_result.setStyleSheet("background:transparent;")
        result_lay = QVBoxLayout(self.zaap_result)
        result_lay.setContentsMargins(0, 0, 0, 0)
        result_lay.setSpacing(10)

        name_row = QHBoxLayout()
        name_row.setSpacing(8)
        icon_lbl = QLabel()
        zaap_icon = load_icon("icon_zaap.png", 26)
        if zaap_icon:
            icon_lbl.setPixmap(zaap_icon.pixmap(26, 26))
        icon_lbl.setStyleSheet("background:transparent;")
        name_row.addWidget(icon_lbl)
        self.zaap_name_lbl = QLabel()
        self.zaap_name_lbl.setStyleSheet(f"font-size:13px; font-weight:700; color:{TEXT}; background:transparent;")
        self.zaap_name_lbl.setWordWrap(True)
        name_row.addWidget(self.zaap_name_lbl, 1)
        result_lay.addLayout(name_row)

        self.zaap_coord_lbl = QLabel()
        self.zaap_coord_lbl.setStyleSheet(f"font-size:11px; color:{MUT}; background:transparent;")
        result_lay.addWidget(self.zaap_coord_lbl)

        self.zaap_dist_lbl = QLabel()
        self.zaap_dist_lbl.setStyleSheet(f"font-size:11px; color:{MUT}; background:transparent;")
        result_lay.addWidget(self.zaap_dist_lbl)

        self.zaap_cmd_lbl = QLabel()
        self.zaap_cmd_lbl.setFont(mono(11))
        self.zaap_cmd_lbl.setObjectName("ZaapCmd")
        self.zaap_cmd_lbl.setStyleSheet(
            f"QLabel#ZaapCmd{{background:{BG3}; color:{ACC}; border-radius:5px; padding:5px 8px;}}"
        )
        self.zaap_cmd_lbl.setWordWrap(True)
        result_lay.addWidget(self.zaap_cmd_lbl)

        box_lay.addWidget(self.zaap_result)
        self.zaap_result.setVisible(False)
        self.zaap_error_lbl = QLabel()
        self.zaap_error_lbl.setStyleSheet("font-size:12px; color:#ff5c5c; background:transparent;")
        self.zaap_error_lbl.setWordWrap(True)
        self.zaap_error_lbl.setVisible(False)
        box_lay.addWidget(self.zaap_error_lbl)

        clay.addWidget(box)

        self.copy_btn = ghost_btn("📋  Copier la commande /travel", self._copy_travel)
        self.copy_btn.setEnabled(False)
        clay.addWidget(self.copy_btn)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background:{BORDER};")
        clay.addWidget(sep)

        self.auto_chk = QCheckBox("Coller auto + valider dans le chat de :")
        self.auto_chk.setStyleSheet(f"font-size:11px; color:{MUT}; background:transparent;")
        clay.addWidget(self.auto_chk)

        self.char_c = QComboBox()
        self._refresh_accounts()
        clay.addWidget(self.char_c)

        can_auto = bool(self.config and self.logic and PYAUTOGUI_OK)
        self.auto_chk.setEnabled(can_auto)
        self.char_c.setEnabled(can_auto)
        if not can_auto:
            self.auto_chk.setText("Coller auto (indisponible)")

        clay.addStretch()
        return c

    def _refresh_accounts(self):
        self.char_c.clear()
        if not self.logic:
            return
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
            self.status_lbl.setStyleSheet("color:#ff5c5c; font-size:11px; background:transparent;")
            return
        direction = self.direction
        self.results_list.clear()
        self._reset_zaap_box()
        self.copy_btn.setEnabled(False)
        self._travel_cmd = None
        self.search_btn.setEnabled(False)
        self.status_lbl.setText("Recherche en cours...")
        self.status_lbl.setStyleSheet(f"color:{MUT}; font-size:11px; background:transparent;")
        self._search_thread = HintSearchThread(x, y, direction)
        self._search_thread.done.connect(self._on_hints)
        self._search_thread.start()

    def _on_hints(self, hints, error):
        self.search_btn.setEnabled(True)
        if error:
            self.status_lbl.setText(f"❌  Erreur : {error}")
            self.status_lbl.setStyleSheet("color:#ff5c5c; font-size:11px; background:transparent;")
            return
        self._hints = hints
        if not hints:
            self.status_lbl.setText("Aucun indice trouvé dans cette direction.")
            self.status_lbl.setStyleSheet(f"color:{MUT}; font-size:11px; background:transparent;")
            return
        self.status_lbl.setText(f"{len(hints)} indice(s) trouvé(s) — sélectionne le tien.")
        self.status_lbl.setStyleSheet(f"color:{ACC}; font-size:11px; font-weight:600; background:transparent;")
        for h in hints:
            item = QListWidgetItem(f"{h['name']}   ·   {h['dist']} map(s)   ·   ({h['x']}, {h['y']})")
            item.setData(Qt.ItemDataRole.UserRole, h)
            self.results_list.addItem(item)

    def _reset_zaap_box(self):
        self.zaap_placeholder.setText("Sélectionne un indice à gauche\npour voir le zaap le plus proche.")
        self.zaap_placeholder.setVisible(True)
        self.zaap_result.setVisible(False)
        self.zaap_error_lbl.setVisible(False)

    def _select_hint(self, item):
        h = item.data(Qt.ItemDataRole.UserRole)
        if not h or not REQUESTS_OK:
            return
        self.zaap_placeholder.setText("Recherche du zaap le plus proche...")
        self.zaap_placeholder.setVisible(True)
        self.zaap_result.setVisible(False)
        self.zaap_error_lbl.setVisible(False)
        self.copy_btn.setEnabled(False)
        self._zaap_thread = ZaapSearchThread(h["mapId"])
        self._zaap_thread.done.connect(lambda z, err, hh=h: self._on_zaap(hh, z, err))
        self._zaap_thread.start()

    def _on_zaap(self, hint, zaap, error):
        if error or not zaap:
            self.zaap_placeholder.setVisible(False)
            self.zaap_result.setVisible(False)
            self.zaap_error_lbl.setText(f"⚠️  {error or 'Zaap introuvable.'}")
            self.zaap_error_lbl.setVisible(True)
            self.copy_btn.setEnabled(False)
            self._travel_cmd = None
            return
        self._travel_cmd = f"/travel {zaap['x']},{zaap['y']}"
        self.zaap_name_lbl.setText(zaap["name"])
        self.zaap_coord_lbl.setText(f"📍  ({zaap['x']}, {zaap['y']})")
        self.zaap_dist_lbl.setText(f"🧭  {zaap['dist']} map(s) de distance")
        self.zaap_cmd_lbl.setText(self._travel_cmd)
        self.zaap_placeholder.setVisible(False)
        self.zaap_error_lbl.setVisible(False)
        self.zaap_result.setVisible(True)
        self.copy_btn.setEnabled(CLIPBOARD_OK)
        if self.auto_chk.isEnabled() and self.auto_chk.isChecked():
            self._auto_paste()

    def _copy_travel(self):
        if not self._travel_cmd or not CLIPBOARD_OK:
            return
        import pyperclip
        pyperclip.copy(self._travel_cmd)
        self.status_lbl.setText(f"✅  Copié : {self._travel_cmd}")
        self.status_lbl.setStyleSheet(f"color:{ACC}; font-size:11px; font-weight:600; background:transparent;")

    def _auto_paste(self):
        if not self._travel_cmd or not CLIPBOARD_OK or not PYAUTOGUI_OK or not self.logic or not self.config:
            return
        hwnd = self.char_c.currentData()
        if not hwnd:
            self.status_lbl.setText("⚠️  Aucun personnage sélectionné.")
            self.status_lbl.setStyleSheet("color:#ff5c5c; font-size:11px; background:transparent;")
            return
        cp = self.config.get("macro_positions", {}).get("chat_position")
        if not cp:
            self.status_lbl.setText("⚠️  Position du chat non calibrée (bouton CALIB CHAT).")
            self.status_lbl.setStyleSheet("color:#ff5c5c; font-size:11px; background:transparent;")
            return
        import pyperclip
        pyperclip.copy(self._travel_cmd)
        cmd = self._travel_cmd

        def _do():
            try:
                import pyautogui
                self.logic.focus_window(hwnd)
                time.sleep(0.2)
                pyautogui.click(cp[0], cp[1])
                time.sleep(0.15)
                pyautogui.hotkey("ctrl", "v")
                time.sleep(0.08)
                pyautogui.press("enter")
            except Exception as e:
                print(f"[chasse_tresor._auto_paste] {e}")

        threading.Thread(target=_do, daemon=True).start()
        self.status_lbl.setText(f"✅  Collé automatiquement : {cmd}")
        self.status_lbl.setStyleSheet(f"color:{ACC}; font-size:11px; font-weight:600; background:transparent;")
