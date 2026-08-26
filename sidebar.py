"""Sidebar de navigation — remplace le menu "Outils ▾" par une nav groupée.

Widget pur : ne connaît aucune page, ne connaît pas MainWindow. Émet
`sig_navigate(page_key)` quand un item est cliqué ; MainWindow fait le lien
vers le QStackedWidget. objectNames/style déjà prêts dans theme.SIDEBAR_STYLE
(#Sidebar/#SidebarGroupLabel/#SidebarItem + attribut dynamique active=true).
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import pyqtSignal, Qt, QSize

from theme import MUT, mono, load_icon

# (page_key, label, icone optionnelle) groupés par section — l'ordre ici fixe
# l'ordre affiché. L'icône (fichier dans skin/) remplace l'emoji générique
# dans le libellé quand elle est fournie.
ICON_SIZE = 20

GROUPS = [
    ("ORGANISER", [
        ("mes_equipes", "  Mes équipes", "icon_group.png"),
        ("presets", "  Presets d'initiative", "ini.png"),
        ("raccourcis", "⌨  Raccourcis"),
    ]),
    ("OUTILS", [
        ("chasse_tresor", "  Chasse au trésor", "carte.png"),
        ("zaap_menu", "  Zaap", "icon_zaap.png"),
    ]),
    ("SYSTÈME", [
        ("fenetres_scan", "🖥  Gestion"),
        ("calibration", "🎯  Calibration"),
        ("parametres", "⚙  Paramètres"),
    ]),
]

# Entrées qui ne correspondent à aucune page du QStackedWidget — MainWindow
# les intercepte dans _navigate() pour ouvrir un dialog à la place.
NON_PAGE_KEYS = {"parametres"}


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
            for entry in entries:
                key, label = entry[0], entry[1]
                icon_file = entry[2] if len(entry) > 2 else None
                btn = QPushButton(label)
                btn.setObjectName("SidebarItem")
                btn.setProperty("active", "false")
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                if icon_file:
                    icon = load_icon(icon_file, ICON_SIZE)
                    if icon:
                        btn.setIcon(icon)
                        btn.setIconSize(QSize(ICON_SIZE, ICON_SIZE))
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
