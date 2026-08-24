"""Sidebar de navigation — remplace le menu "Outils ▾" par une nav groupée.

Widget pur : ne connaît aucune page, ne connaît pas MainWindow. Émet
`sig_navigate(page_key)` quand un item est cliqué ; MainWindow fait le lien
vers le QStackedWidget. objectNames/style déjà prêts dans theme.SIDEBAR_STYLE
(#Sidebar/#SidebarGroupLabel/#SidebarItem + attribut dynamique active=true).
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import pyqtSignal, Qt

from theme import MUT, mono

# (page_key, label) groupés par section — l'ordre ici fixe l'ordre affiché.
GROUPS = [
    ("ORGANISER", [
        ("mes_equipes", "🏠  Mes équipes"),
        ("presets", "🎯  Presets d'initiative"),
        ("raccourcis", "⌨  Raccourcis"),
    ]),
    ("OUTILS", [
        ("chasse_tresor", "🗺  Chasse au trésor"),
        ("automatisations_zaap", "⚡  Automatisations de zaap"),
    ]),
    ("SYSTÈME", [
        ("fenetres_scan", "🖥  Fenêtres & scan"),
    ]),
]


class Sidebar(QWidget):
    sig_navigate = pyqtSignal(str)

    def __init__(self, version="", parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(210)
        self._items = {}
        self._active = None
        self._build(version)

    def _build(self, version):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 8, 0, 8)
        lay.setSpacing(0)

        for group_label, entries in GROUPS:
            gl = QLabel(group_label)
            gl.setObjectName("SidebarGroupLabel")
            lay.addWidget(gl)
            for key, label in entries:
                btn = QPushButton(label)
                btn.setObjectName("SidebarItem")
                btn.setProperty("active", "false")
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.clicked.connect(lambda _, k=key: self.sig_navigate.emit(k))
                lay.addWidget(btn)
                self._items[key] = btn

        lay.addStretch()

        foot = QLabel(version or "")
        foot.setFont(mono(9))
        foot.setStyleSheet(f"color:{MUT}; background:transparent; padding:6px 16px;")
        lay.addWidget(foot)

    def set_active(self, page_key):
        if self._active == page_key:
            return
        if self._active in self._items:
            btn = self._items[self._active]
            btn.setProperty("active", "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        if page_key in self._items:
            btn = self._items[page_key]
            btn.setProperty("active", "true")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self._active = page_key
