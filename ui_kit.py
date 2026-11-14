"""Kit d'interface commun : fenêtres (DtDialog), boîtes de message/saisie, barre de titre sombre, style applicatif.

Avant : chaque fenêtre avait sa propre mise en page (certaines sans titre, boutons dorés ici, orange là), les confirmations
étaient des QMessageBox natifs en anglais (« Yes / No ») et la barre de titre Windows restait blanche. Tout passe désormais par
ici : même en-tête (icône, titre, sous-titre), même pied de page (actions à droite, l'action principale en accent), même
vocabulaire en français.

    dlg = DtDialog(parent, "Preset d'initiative", "Choisis l'ordre des personnages", icon="icon_group.png")
    dlg.body.addWidget(...)
    dlg.add_button("Annuler", "ghost", dlg.reject)
    dlg.add_button("Sauvegarder", "primary", dlg.accept)

    if confirm(self, "Supprimer le preset", "« Raid » sera supprimé.", ok="Supprimer", danger=True): ...
"""
from __future__ import annotations

import ctypes
import sys

from PyQt6.QtCore import Qt, QObject, QEvent, QSize
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget, QFrame,
                             QLineEdit, QComboBox, QSizePolicy)

from paths import SKIN_DIR
from theme import (STYLE, BG, BG2, BG3, BG4, ACC, RED, GREEN, BLUE, GOLD, TEXT, MUT, GHOST, BORDER, BORDER2, BORDER3)

# ── Style applicatif ────────────────────────────────────────────────────────────
# Appliqué à QApplication : il couvre les fenêtres qui ne descendent pas de la fenêtre principale (menus, infobulles,
# boîtes de dialogue). Volontairement SANS règle `QWidget {background}` : cela casserait les overlays translucides.
APP_STYLE = f"""
QToolTip {{ background:{BG2}; color:{TEXT}; border:1px solid {BORDER3}; border-radius:8px; padding:6px 10px;
            font-family:'DM Sans','Segoe UI',sans-serif; font-size:12px; }}
QMenu {{ background:{BG2}; color:{TEXT}; border:1px solid {BORDER3}; border-radius:12px; padding:6px;
         font-family:'DM Sans','Segoe UI',sans-serif; }}
QMenu::item {{ padding:8px 22px 8px 14px; border-radius:8px; font-size:13px; font-weight:600; margin:1px 0; }}
QMenu::item:selected {{ background:rgba(255,138,30,0.14); color:{ACC}; }}
QMenu::item:disabled {{ color:{GHOST}; }}
QMenu::separator {{ background:{BORDER}; height:1px; margin:5px 8px; }}
QMenu::indicator {{ width:14px; height:14px; margin-left:6px; }}
QDialog {{ background:{BG}; color:{TEXT}; }}
QDialog QLabel {{ color:{TEXT}; background:transparent; }}
"""


# ── Barre de titre sombre (Windows 10/11) ───────────────────────────────────────
def dark_titlebar(widget):
    """Barre de titre native sombre + couleur d'en-tête DofusTeam (Windows 11). Sans effet ailleurs."""
    if sys.platform != "win32":
        return
    try:
        hwnd = int(widget.winId())
        dwm = ctypes.windll.dwmapi
        one = ctypes.c_int(1)
        for attr in (20, 19):                                   # USE_IMMERSIVE_DARK_MODE (nouveau / ancien numéro)
            dwm.DwmSetWindowAttribute(hwnd, attr, ctypes.byref(one), 4)
        for attr, rgb in ((35, BG2), (36, TEXT)):               # couleur de barre / de texte (Windows 11)
            r, g, b = (int(rgb.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
            col = ctypes.c_int(r | (g << 8) | (b << 16))
            dwm.DwmSetWindowAttribute(hwnd, attr, ctypes.byref(col), 4)
    except Exception:
        pass


class _ChromeFilter(QObject):
    """Applique la barre de titre sombre à chaque fenêtre de premier niveau à son premier affichage."""

    def eventFilter(self, obj, ev):
        if ev.type() == QEvent.Type.Show and isinstance(obj, QWidget) and obj.isWindow():
            if not (obj.windowFlags() & Qt.WindowType.FramelessWindowHint) and not obj.property("_dt_titlebar"):
                obj.setProperty("_dt_titlebar", True)
                dark_titlebar(obj)
        return False


_filter = None


def install_app_chrome(app: QApplication):
    """À appeler une fois au démarrage : style applicatif + barres de titre sombres."""
    global _filter
    app.setStyleSheet(APP_STYLE)
    _filter = _ChromeFilter(app)
    app.installEventFilter(_filter)


# ── Boutons ─────────────────────────────────────────────────────────────────────
def make_button(text: str, role: str = "ghost", slot=None, min_width: int = 0) -> QPushButton:
    """role : primary (action principale, accent) | danger (destructif) | ghost (secondaire)."""
    b = QPushButton(text)
    b.setProperty("role", role)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setMinimumHeight(34)
    if min_width:
        b.setMinimumWidth(min_width)
    if slot is not None:
        b.clicked.connect(lambda _=False: slot())
    return b


# ── Fenêtre standard ────────────────────────────────────────────────────────────
class DtDialog(QDialog):
    """Fenêtre à la structure commune : en-tête (icône, titre, sous-titre) / corps / pied de page (actions)."""

    def __init__(self, parent=None, title="", subtitle="", icon=None, width=0, height=0, resizable=False, modal=True):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(modal)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        self.setObjectName("DtDialog")
        if width and height:
            (self.resize if resizable else self.setFixedSize)(width, height)
        elif width:
            self.setMinimumWidth(width)
        self.setStyleSheet(STYLE + self._qss())

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # En-tête
        self.header = QFrame()
        self.header.setObjectName("DtHeader")
        hl = QHBoxLayout(self.header)
        hl.setContentsMargins(22, 16, 22, 14)
        hl.setSpacing(12)
        if icon:
            ic = QLabel()
            ic.setFixedSize(34, 34)
            ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pm = QPixmap(str(SKIN_DIR / icon))
            if not pm.isNull():
                ic.setPixmap(pm.scaled(26, 26, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            ic.setObjectName("DtHeaderIcon")
            hl.addWidget(ic)
        col = QVBoxLayout()
        col.setSpacing(1)
        self.title_lbl = QLabel(title)
        self.title_lbl.setObjectName("DtTitle")
        col.addWidget(self.title_lbl)
        self.subtitle_lbl = QLabel(subtitle)
        self.subtitle_lbl.setObjectName("DtSubtitle")
        self.subtitle_lbl.setWordWrap(True)
        self.subtitle_lbl.setVisible(bool(subtitle))
        col.addWidget(self.subtitle_lbl)
        hl.addLayout(col, 1)
        root.addWidget(self.header)

        # Corps
        self.body_frame = QFrame()
        self.body_frame.setObjectName("DtBody")
        self.body = QVBoxLayout(self.body_frame)
        self.body.setContentsMargins(22, 18, 22, 18)
        self.body.setSpacing(12)
        root.addWidget(self.body_frame, 1)

        # Pied de page
        self.footer_frame = QFrame()
        self.footer_frame.setObjectName("DtFooter")
        self.footer = QHBoxLayout(self.footer_frame)
        self.footer.setContentsMargins(22, 12, 22, 14)
        self.footer.setSpacing(8)
        self.footer.addStretch()
        root.addWidget(self.footer_frame)
        self.footer_frame.hide()

    @staticmethod
    def _qss():
        return f"""
        QDialog#DtDialog {{ background:{BG}; }}
        QFrame#DtHeader {{ background:{BG2}; border:none; border-bottom:1px solid {BORDER}; }}
        QFrame#DtBody {{ background:{BG}; border:none; }}
        QFrame#DtFooter {{ background:{BG2}; border:none; border-top:1px solid {BORDER}; }}
        QLabel#DtTitle {{ background:transparent; color:{TEXT}; font-size:16px; font-weight:700; }}
        QLabel#DtSubtitle {{ background:transparent; color:{MUT}; font-size:12px; }}
        QLabel#DtHeaderIcon {{ background:{BG3}; border:1px solid {BORDER}; border-radius:9px; }}
        """

    def add_button(self, text, role="ghost", slot=None, min_width=96) -> QPushButton:
        self.footer_frame.show()
        b = make_button(text, role, slot, min_width)
        self.footer.addWidget(b)
        if role == "primary":
            b.setDefault(True)
        return b

    def set_footer_hint(self, text: str):
        """Texte discret à gauche du pied de page (ex. un compteur)."""
        self.footer_frame.show()
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color:{MUT}; font-size:11px; background:transparent;")
        self.footer.insertWidget(0, lbl)
        return lbl

    def section(self, text: str) -> QLabel:
        """Petit titre de section (majuscules espacées) à insérer dans le corps."""
        lbl = QLabel(text.upper())
        lbl.setStyleSheet(f"color:{MUT}; font-size:10px; font-weight:700; letter-spacing:1.4px; background:transparent;")
        return lbl

    def center_on(self, parent):
        if parent is not None:
            g = parent.window().frameGeometry()
            self.move(g.center() - self.rect().center())


# ── Boîtes de message ───────────────────────────────────────────────────────────
_LEVELS = {
    "info": ("i", BLUE),
    "warn": ("!", GOLD),
    "error": ("✕", RED),
    "ask": ("?", ACC),
}


def _message(parent, level, title, text, buttons, danger=False, default=None):
    """buttons : liste de (texte, role, valeur). Retourne la valeur du bouton cliqué (None si fermée)."""
    glyph, color = _LEVELS[level]
    dlg = DtDialog(parent, title)
    dlg.header.hide()
    dlg.setMinimumWidth(380)
    dlg.setMaximumWidth(520)
    dlg.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
    row = QHBoxLayout()
    row.setSpacing(14)
    badge = QLabel(glyph)
    badge.setFixedSize(40, 40)
    badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
    badge.setStyleSheet(f"background:rgba(255,255,255,0.04); color:{color}; border:1px solid {color}; border-radius:20px; "
                        f"font-size:18px; font-weight:800;")
    row.addWidget(badge, 0, Qt.AlignmentFlag.AlignTop)
    col = QVBoxLayout()
    col.setSpacing(5)
    t = QLabel(title)
    t.setWordWrap(True)
    t.setStyleSheet(f"color:{TEXT}; font-size:15px; font-weight:700; background:transparent;")
    col.addWidget(t)
    if text:
        m = QLabel(text)
        m.setWordWrap(True)
        m.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        m.setStyleSheet(f"color:{MUT}; font-size:12.5px; background:transparent;")
        col.addWidget(m)
    row.addLayout(col, 1)
    dlg.body.addLayout(row)
    result = {"v": None}

    def pick(v):
        result["v"] = v
        dlg.accept()
    for label, role, value in buttons:
        dlg.add_button(label, role, lambda v=value: pick(v))
    dlg.adjustSize()
    dlg.exec()
    return result["v"]


def info(parent, title, text=""):
    _message(parent, "info", title, text, [("OK", "primary", True)])


def warn(parent, title, text=""):
    _message(parent, "warn", title, text, [("OK", "primary", True)])


def error(parent, title, text=""):
    _message(parent, "error", title, text, [("OK", "primary", True)])


def confirm(parent, title, text="", ok="Confirmer", cancel="Annuler", danger=False) -> bool:
    return bool(_message(parent, "warn" if danger else "ask", title, text,
                         [(cancel, "ghost", False), (ok, "danger" if danger else "primary", True)]))


def ask_text(parent, title, label="", text="", placeholder="", ok="Valider", subtitle="") -> str | None:
    """Saisie d'un texte ; None si annulé ou vide."""
    dlg = DtDialog(parent, title, subtitle or label, width=420)
    edit = QLineEdit(text)
    edit.setPlaceholderText(placeholder)
    edit.setMinimumHeight(36)
    dlg.body.addWidget(edit)
    dlg.add_button("Annuler", "ghost", dlg.reject)
    dlg.add_button(ok, "primary", dlg.accept)
    edit.returnPressed.connect(dlg.accept)
    edit.setFocus()
    if dlg.exec() and edit.text().strip():
        return edit.text().strip()
    return None


def ask_choice(parent, title, label, items, current=0, ok="Valider", extra=None) -> str | None:
    """Choix dans une liste. `extra` = libellé d'une entrée supplémentaire (ex. « ＋ Nouveau pack… »)."""
    dlg = DtDialog(parent, title, label, width=420)
    combo = QComboBox()
    combo.setMinimumHeight(36)
    for it in items:
        combo.addItem(it)
    if extra:
        combo.addItem(extra)
    combo.setCurrentIndex(max(0, min(current, combo.count() - 1)))
    dlg.body.addWidget(combo)
    dlg.add_button("Annuler", "ghost", dlg.reject)
    dlg.add_button(ok, "primary", dlg.accept)
    if dlg.exec():
        return combo.currentText()
    return None
