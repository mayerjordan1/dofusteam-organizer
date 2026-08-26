"""Design system partagé DofusTeam Organizer — une seule source de vérité.

Avant : chaque fichier (main/hunt/calibrator/char_selector/invite_dialog/
zaap_dialog/zaap_favorites) redéfinissait sa propre palette + son propre
STYLE + son propre make_avatar(), avec des variations qui divergeaient au
fil des sessions. Tout le monde importe désormais ce module.
"""
from PyQt6.QtWidgets import QPushButton, QLabel, QApplication
from PyQt6.QtGui import QPixmap, QFont, QIcon
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from paths import SKIN_DIR

# ── Palette (alignée sur dofus-team/app/globals.css) ───────────────────────────
BG     = "#0f1115"
BG2    = "#151922"
BG3    = "#1b2130"
BG4    = "#232a3d"
ACC    = "#ff8a1e"
RED    = "#e05555"
GREEN  = "#3fb950"
GOLD   = "#c8a000"
BLUE   = "#4fa3e0"
TEXT   = "#f3f4f6"
MUT    = "#9ca3af"
BORDER = "rgba(255,255,255,0.08)"

# ── Feuille de style globale ────────────────────────────────────────────────────
# Principes : un seul accent (utilisé pour l'action principale + focus/actif),
# le reste reste neutre. Space Mono réservé aux valeurs numériques/compteurs.
STYLE = f"""
QWidget {{ background:{BG}; color:{TEXT}; font-family:'Segoe UI',sans-serif; font-size:13px; }}
QMainWindow, QDialog {{ background:{BG}; }}
QScrollArea {{ background:transparent; border:none; }}
QScrollBar:vertical {{ background:{BG2}; width:4px; border-radius:2px; margin:0; }}
QScrollBar::handle:vertical {{ background:{BG4}; border-radius:2px; min-height:20px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}
QPushButton {{ background:{BG3}; color:{TEXT}; border:1px solid {BORDER};
               border-radius:6px; padding:5px 12px; font-size:12px; }}
QPushButton:hover {{ background:{BG4}; border-color:rgba(255,255,255,0.16); }}
QPushButton:pressed {{ background:{BG2}; }}
QLineEdit {{ background:{BG2}; color:{TEXT}; border:1px solid {BORDER};
             border-radius:6px; padding:5px 10px; }}
QLineEdit:focus {{ border-color:{ACC}; }}
QComboBox {{ background:{BG3}; color:{TEXT}; border:1px solid {BORDER};
             border-radius:6px; padding:4px 10px; }}
QComboBox::drop-down {{ border:none; width:20px; }}
QComboBox QAbstractItemView {{ background:{BG2}; color:{TEXT};
    selection-background-color:{BG3}; border:1px solid {BORDER}; }}
QListWidget {{ background:{BG2}; border:1px solid {BORDER}; border-radius:8px; }}
QListWidget::item {{ padding:6px; border-radius:5px; }}
QListWidget::item:selected {{ background:rgba(255,138,30,0.14); color:{ACC}; }}
QSlider::groove:horizontal {{ height:3px; background:{BG3}; border-radius:2px; }}
QSlider::handle:horizontal {{ background:{ACC}; width:12px; height:12px; border-radius:6px; margin:-5px 0; }}
QSlider::sub-page:horizontal {{ background:{ACC}; border-radius:2px; }}
QCheckBox {{ spacing:6px; }}
QCheckBox::indicator {{ width:15px; height:15px; border-radius:4px;
    border:1px solid rgba(255,255,255,0.15); background:{BG2}; }}
QCheckBox::indicator:checked {{ background:{ACC}; border-color:{ACC}; }}
QMenu {{ background:{BG2}; color:{TEXT}; border:1px solid {BORDER}; border-radius:8px; padding:4px; }}
QMenu::item {{ padding:6px 20px; border-radius:5px; }}
QMenu::item:selected {{ background:{BG3}; color:{ACC}; }}
QMenu::separator {{ background:{BORDER}; height:1px; margin:4px 8px; }}
QToolTip {{ background:{BG2}; color:{TEXT}; border:1px solid rgba(255,255,255,0.1);
            border-radius:5px; padding:4px 8px; font-size:11px; }}
QStackedWidget > QWidget {{ background:transparent; }}
"""


# ── Chrome additif : sidebar de navigation + header de page ────────────────────
# Additif uniquement — ne redéfinit aucune couleur existante, juste des règles
# de style scoped par objectName pour la nouvelle nav (sidebar + QStackedWidget).
SIDEBAR_STYLE = f"""
#Sidebar {{ background:{BG2}; border-right:1px solid {BORDER}; }}
#SidebarGroupLabel {{ color:{MUT}; font-size:10px; font-weight:700; letter-spacing:1.5px;
    background:transparent; padding:14px 16px 4px 16px; }}
#SidebarItem {{ background:transparent; color:{MUT}; border:none; border-radius:8px;
    text-align:left; padding:8px 14px; font-size:12.5px; font-weight:600; }}
#SidebarItem:hover {{ background:{BG3}; color:{TEXT}; }}
#SidebarItem[active="true"] {{ background:rgba(255,138,30,0.12); color:{ACC}; }}
#PageHeader {{ background:transparent; border-bottom:1px solid {BORDER}; }}
#PageTitle {{ color:{TEXT}; font-size:16px; font-weight:700; font-family:'Space Mono',monospace;
    background:transparent; }}
#PageSubtitle {{ color:{MUT}; font-size:11px; background:transparent; }}
"""


def mono(size=11, bold=False):
    f = QFont("Space Mono", size)
    f.setBold(bold)
    return f


def section_label(text):
    """Titre de section discret — sans puce, séparation par soulignement fin."""
    lbl = QLabel(text.upper())
    lbl.setFont(mono(9, True))
    lbl.setStyleSheet(f"color:{MUT}; letter-spacing:1.5px; background:transparent;")
    return lbl


_card_seq = [0]


def card(widget):
    """Fond + bordure appliqués uniquement au conteneur — jamais aux enfants.

    Piège Qt : un style non scopé (widget.setStyleSheet("border:...;")) cascade
    vers tous les descendants sans leur propre "border:none" (QLabel, etc.),
    ce qui dessinait un rectangle/rond parasite autour de chaque texte enfant.
    Scoper via #objectName isole la règle au widget ciblé."""
    _card_seq[0] += 1
    name = f"Card{_card_seq[0]}"
    widget.setObjectName(name)
    widget.setStyleSheet(f"QWidget#{name} {{ background:{BG2}; border:1px solid {BORDER}; border-radius:10px; }}")
    return widget


def _hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def glass_card(widget, alpha=0.5):
    """Variante translucide de card() — laisse deviner le fond animé derrière
    (pas de vrai flou, Qt Stylesheets ne le supporte pas, mais la teinte
    semi-transparente + liseré clair suffit à donner l'effet verre).

    Scopé via #objectName (voir card()) pour ne pas faire hériter le border/
    background aux QLabel/QCheckBox enfants."""
    _card_seq[0] += 1
    name = f"Card{_card_seq[0]}"
    widget.setObjectName(name)
    r, g, b = _hex_to_rgb(BG2)
    widget.setStyleSheet(
        f"QWidget#{name} {{ background: rgba({r},{g},{b},{alpha}); "
        f"border: 1px solid rgba(255,255,255,0.10); border-radius:12px; }}"
    )
    return widget


_icon_cache = {}


def load_icon(filename, size=18):
    """Charge une icône PNG depuis skin/ (mise en cache, redimensionnée)."""
    key = (filename, size)
    if key in _icon_cache:
        return _icon_cache[key]
    p = SKIN_DIR / filename
    if not p.exists():
        return None
    pix = QPixmap(str(p))
    if pix.isNull():
        return None
    pix = pix.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    icon = QIcon(pix)
    _icon_cache[key] = icon
    return icon


_CROWN_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="{color}">
<path d="M3 8.5l4.2 3 4.8-6.5 4.8 6.5 4.2-3-1.6 9.5H4.6L3 8.5z"/>
<rect x="4.3" y="19" width="15.4" height="2.2" rx="1.1"/>
</svg>"""

_svg_icon_cache = {}


def svg_pixmap(svg_source, size=16, color=GOLD):
    """Rasterise un SVG inline (mise en cache) — évite de bundler un fichier .svg."""
    key = (svg_source, size, color)
    if key in _svg_icon_cache:
        return _svg_icon_cache[key]
    from PyQt6.QtSvg import QSvgRenderer
    from PyQt6.QtGui import QPainter
    data = svg_source.format(color=color).encode("utf-8")
    renderer = QSvgRenderer(data)
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    renderer.render(painter)
    painter.end()
    _svg_icon_cache[key] = pix
    return pix


def crown_icon(size=16, color=GOLD):
    """Icône couronne (SVG rasterisé) — utilisée pour marquer le chef de groupe."""
    return svg_pixmap(_CROWN_SVG, size, color)


def accent_btn(text, fn, color=ACC, icon_file=None, icon_size=22):
    b = QPushButton(text)
    padding = f"8px 16px 8px 12px" if icon_file else "6px 16px"
    b.setStyleSheet(
        f"background:{color}; color:#0f1115; border:none; border-radius:6px;"
        f"padding:{padding}; font-weight:700; font-size:12px;"
    )
    if icon_file:
        icon = load_icon(icon_file, icon_size)
        if icon:
            b.setIcon(icon)
            b.setIconSize(QSize(icon_size, icon_size))
    b.clicked.connect(fn)
    return b


def ghost_btn(text, fn):
    b = QPushButton(text)
    b.setStyleSheet(
        f"background:transparent; color:{MUT}; border:1px solid {BORDER};"
        f"border-radius:6px; padding:5px 12px; font-size:12px;"
    )
    b.clicked.connect(fn)
    return b


class ClickableAvatar(QLabel):
    """QLabel d'avatar cliquable — utilisé pour basculer homme/femme au clic.

    Le clic n'est émis qu'au relâchement, et seulement si la souris n'a pas
    bougé au-delà du seuil de drag — sinon un glisser-déposer démarré depuis
    l'avatar (le parent gère le drag via l'event qui remonte, non accepté ici)
    basculait aussi le sexe du personnage à chaque tentative de drag."""
    clicked = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._press_pos = None

    def mousePressEvent(self, event):
        self._press_pos = event.position().toPoint()
        event.ignore()

    def mouseReleaseEvent(self, event):
        if self._press_pos is not None:
            moved = (event.position().toPoint() - self._press_pos).manhattanLength()
            if moved < QApplication.startDragDistance():
                self.clicked.emit()
        self._press_pos = None
        event.ignore()


_avatar_cache = {}


def make_avatar(classe, size=36, sexe="h"):
    if not classe:
        return None
    key = (classe.lower(), size, sexe)
    if key in _avatar_cache:
        return _avatar_cache[key]
    p = SKIN_DIR / f"{classe.lower()}_{sexe}.png"
    if not p.exists():
        p = SKIN_DIR / f"{classe.lower()}.png"
    if not p.exists():
        return None
    pix = QPixmap(str(p))
    if pix.isNull():
        return None
    scaled = pix.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    _avatar_cache[key] = scaled
    return scaled
