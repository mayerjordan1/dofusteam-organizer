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
        ("raccourcis", "  Raccourcis", "icon_keys.png"),
    ]),
    ("OUTILS", [
        ("chasse_tresor", "  Chasse au trésor", "carte.png"),
        ("pnj", "  PNJ", "icon_dofusteam.png"),
        ("zaap_menu", "  Zaap", "icon_zaap.png"),
    ]),
    ("DONJON", [
        ("donjons", "  Donjons", "donjon.png"),
    ]),
    ("CLASSES", [
        ("classes", "  Classes", "huppermage.png"),
    ]),
    ("SYSTÈME", [
        ("calibration", "  Calibration", "icon_calib.png"),
        ("parametres", "  Paramètres", "icon_settings.png"),
    ]),
]

# Entrées qui ne correspondent à aucune page du QStackedWidget — MainWindow
# les intercepte dans _navigate() pour ouvrir un dialog à la place.
NON_PAGE_KEYS = {"parametres", "chasse_tresor", "pnj"}


def _square_icon(filename, size):
    """Icône centrée dans un carré fixe : sans ça, une icône étroite (l'œuf DofusTeam) décale son libellé par rapport aux autres."""
    from PyQt6.QtGui import QPixmap, QPainter, QIcon
    from paths import SKIN_DIR
    pm = QPixmap(str(SKIN_DIR / filename))
    if pm.isNull():
        return None
    pm = pm.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    out = QPixmap(size, size)
    out.fill(Qt.GlobalColor.transparent)
    p = QPainter(out)
    p.drawPixmap((size - pm.width()) // 2, (size - pm.height()) // 2, pm)
    p.end()
    return QIcon(out)


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
        lay.setContentsMargins(10, 8, 10, 8)   # boutons inset : plus de pastilles collées aux bords
        lay.setSpacing(2)

        for group_label, entries in GROUPS:
            gl = QLabel(group_label)
            gl.setObjectName("SidebarGroupLabel")
            lay.addWidget(gl)
            for entry in entries:
                key, label = entry[0], entry[1]
                icon_file = entry[2] if len(entry) > 2 else None
                btn = QPushButton("  " + label.strip())      # libellés normalisés (un seul espace d'icône pour tous)
                btn.setObjectName("SidebarItem")
                btn.setProperty("active", "false")
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                if icon_file:
                    icon = _square_icon(icon_file, ICON_SIZE)
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
