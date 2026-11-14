"""Briques de l'overlay PNJ : thèmes, vignettes, carte de PNJ, grille adaptative, boîtes de dialogue.

La carte reprend celle de la page /pnj du site : vignette, nom, pastille de zone colorée à droite du nom,
bloc « Position » (coordonnées en gros), bloc « Zaap », bouton « Copier » (la commande reste en infobulle).
Tous les petits textes sont en sans-serif (jamais de mono). Aucune frappe n'est envoyée au jeu : on copie seulement.
"""
from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtCore import Qt, QObject, QRunnable, QThreadPool, QSize, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap, QColor
from PyQt6.QtWidgets import (
    QWidget, QFrame, QLabel, QHBoxLayout, QVBoxLayout, QGridLayout, QPushButton, QDialog, QSpinBox, QLineEdit,
    QComboBox, QFormLayout, QDialogButtonBox, QSizePolicy,
)

import pnj_data
from ui_kit import DtDialog
from paths import SKIN_DIR
from pnj_engine import Result, zone_hue

FONT = "'DM Sans','Segoe UI',sans-serif"


# ── Thèmes ──────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Theme:
    key: str
    label: str
    bg: str
    bg2: str
    bg3: str
    bg4: str
    acc: str
    text: str
    mut: str
    ghost: str
    border: str


THEMES = {t.key: t for t in [
    Theme("dofusteam", "DofusTeam", "#0d1117", "#161b22", "#1c2128", "#252d38", "#ff8a1e", "#e8e9ed", "#7a7d8a", "#3d4250", "rgba(255,255,255,0.09)"),
    Theme("citron", "Citron", "#0d1117", "#161b22", "#1c2128", "#252d38", "#c8f135", "#e8e9ed", "#7a7d8a", "#3d4250", "rgba(255,255,255,0.09)"),
    Theme("minuit", "Minuit", "#0b1020", "#121a30", "#18223d", "#223052", "#4fa3e0", "#e6edf7", "#7f8aa3", "#38435f", "rgba(160,190,255,0.12)"),
    Theme("foret", "Forêt", "#0c130f", "#131d17", "#1a271f", "#243529", "#6dc96d", "#e5eee7", "#7d8f82", "#3a4a3f", "rgba(180,255,200,0.10)"),
    Theme("clair", "Clair", "#f3f4f7", "#ffffff", "#e9ebf0", "#dde0e8", "#d9690a", "#1b1f27", "#5d6575", "#b4bac6", "rgba(0,0,0,0.12)"),
]}


def theme_of(key: str) -> Theme:
    return THEMES.get(key) or THEMES["dofusteam"]


# Icônes du jeu disponibles (skin/). Les champs sans icône du jeu sont listés ici pour être signalés.
ICON_ZAAP = "icon_zaap.png"
ICON_POSITION = "carte.png"
ICON_FILES = {"Position": ICON_POSITION, "Zaap": ICON_ZAAP, "Réglages": "icon_settings.png", "Convoi": "icon_group.png"}
ICONS_MISSING = ["Opacité", "Thème", "Langue", "Anti lag", "Raccourci", "Recherche", "Favoris (étoile)",
                 "Positions perso : champ / atelier / banque"]
CUSTOM_ICON_CHOICES = [("Position", "carte.png"), ("Zaap", "icon_zaap.png"), ("Donjon", "donjon.png"),
                       ("Groupe", "icon_group.png"), ("Déplacement", "deplacement.png")]

_pix_cache: dict = {}


def skin_pixmap(name: str, size: int) -> QPixmap:
    key = (name, size)
    if key not in _pix_cache:
        p = QPixmap(str(SKIN_DIR / name))
        _pix_cache[key] = p.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation) if not p.isNull() else QPixmap()
    return _pix_cache[key]


def icon_label(name: str, size: int) -> QLabel:
    lbl = QLabel()
    lbl.setFixedSize(size, size)
    lbl.setPixmap(skin_pixmap(name, size))
    lbl.setStyleSheet("background:transparent; border:none;")
    return lbl


# ── Vignettes (téléchargées à la demande, hors thread d'interface) ──────────────
class _Signals(QObject):
    done = pyqtSignal(str)


class _Fetch(QRunnable):
    def __init__(self, rel, sig):
        super().__init__()
        self.rel, self.sig = rel, sig

    def run(self):
        pnj_data.fetch_image(self.rel)
        try:
            self.sig.done.emit(self.rel)
        except RuntimeError:   # fenêtre déjà fermée
            pass


class Thumbs(QObject):
    """Cache de vignettes. get(rel, size) rend un pixmap (ou None) et demande le téléchargement si besoin."""
    loaded = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._pending: set = set()
        self._missing: set = set()
        self._sig = _Signals()
        self._sig.done.connect(self._on_done)
        self._pool = QThreadPool()
        self._pool.setMaxThreadCount(3)

    def get(self, rel: str, size: int):
        p = pnj_data.image_path(rel)
        if p:
            pm = QPixmap(str(p))
            if not pm.isNull():
                return pm.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        if rel not in self._pending and rel not in self._missing:
            self._pending.add(rel)
            self._pool.start(_Fetch(rel, self._sig))
        return None

    def _on_done(self, rel):
        self._pending.discard(rel)
        if not pnj_data.image_path(rel):
            self._missing.add(rel)  # 15 PNJ n'ont pas de vignette : on ne réessaie pas
        self.loaded.emit(rel)


# ── Carte de PNJ ────────────────────────────────────────────────────────────────
class PnjCard(QFrame):
    """Une carte. `s` = facteur d'échelle (suit la taille de la fenêtre)."""
    copy_requested = pyqtSignal(object)      # Result
    fav_toggled = pyqtSignal(object)
    menu_requested = pyqtSignal(object, object)  # Result, point global
    selected = pyqtSignal(object)

    def __init__(self, r: Result, th: Theme, s: float, thumbs: Thumbs, cmd: str, mode_label: str,
                 is_fav=False, corrected=False, icon_override=None, left_widget=None, parent=None):
        super().__init__(parent)
        self.r, self.th, self.s, self.cmd = r, th, s, cmd
        self._thumbs = thumbs
        self._icon_override = icon_override
        self._thumb_size = int(64 * s)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(cmd)
        self.setObjectName("PnjCard")
        self.set_selected(False)

        outer = QVBoxLayout(self)
        m = int(12 * s)
        outer.setContentsMargins(m, m, m, m)
        outer.setSpacing(int(10 * s))

        top = QHBoxLayout()
        top.setSpacing(int(10 * s))
        if left_widget is not None:
            top.addWidget(left_widget)
        self.thumb = QLabel()
        self.thumb.setFixedSize(self._thumb_size, self._thumb_size)
        self.thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb.setStyleSheet(f"background:{th.bg3}; border:none; border-radius:{int(8 * s)}px;")
        self._set_thumb()
        top.addWidget(self.thumb)

        name = QLabel(r.name)
        name.setWordWrap(True)
        name.setStyleSheet(f"background:transparent; border:none; color:{th.text}; font-family:{FONT}; "
                           f"font-size:{int(14 * s)}px; font-weight:700;")
        top.addWidget(name, 1)
        if r.area:
            h = zone_hue(r.area)
            chip = QLabel(r.area)
            chip.setMaximumWidth(int(170 * s))
            chip.setStyleSheet(
                f"color:hsl({h},75%,{40 if th.key == 'clair' else 72}%); background:hsla({h},55%,45%,0.16); "
                f"border:1px solid hsla({h},55%,55%,0.35); border-radius:{int(8 * s)}px; "
                f"padding:{int(2 * s)}px {int(8 * s)}px; font-family:{FONT}; font-size:{int(11 * s)}px; font-weight:600;")
            top.addWidget(chip, 0, Qt.AlignmentFlag.AlignTop)
        self.star = QPushButton("★" if is_fav else "☆")
        self.star.setFlat(True)
        self.star.setFixedSize(int(26 * s), int(26 * s))
        self.star.setCursor(Qt.CursorShape.PointingHandCursor)
        self.star.setToolTip("Favori")
        self.star.setStyleSheet(f"QPushButton{{background:transparent; border:none; font-size:{int(18 * s)}px; "
                                f"color:{th.acc if is_fav else th.ghost};}}")
        self.star.clicked.connect(lambda: self.fav_toggled.emit(self.r))
        top.addWidget(self.star, 0, Qt.AlignmentFlag.AlignTop)
        outer.addLayout(top)

        row = QHBoxLayout()
        row.setSpacing(int(8 * s))
        row.addWidget(self._block("Position", f"{r.x}  ,  {r.y}", ICON_POSITION, th.acc, corrected), 1)
        if r.zaap:
            row.addWidget(self._block("Zaap", f"{r.zaap.x}  ,  {r.zaap.y}", ICON_ZAAP, th.text, False), 1)
        self.btn = QPushButton(f"Copier {mode_label}")
        self.btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn.setMinimumWidth(int(92 * s))
        self.btn.setStyleSheet(
            f"QPushButton{{background:transparent; color:{th.text}; border:1px solid {th.border}; "
            f"border-radius:{int(8 * s)}px; font-family:{FONT}; font-size:{int(12 * s)}px; font-weight:600; padding:0 {int(10 * s)}px;}}"
            f"QPushButton:hover{{border-color:{th.acc}; color:{th.acc};}}")
        self.btn.clicked.connect(lambda: self.copy_requested.emit(self.r))
        row.addWidget(self.btn)
        outer.addLayout(row)

    def _block(self, title, value, icon, value_color, corrected):
        b = QFrame()
        b.setStyleSheet(f"QFrame{{background:{self.th.bg3}; border:none; border-radius:{int(8 * self.s)}px;}}")
        lay = QVBoxLayout(b)
        lay.setContentsMargins(int(10 * self.s), int(6 * self.s), int(10 * self.s), int(6 * self.s))
        lay.setSpacing(1)
        t = QLabel(title.upper() + ("  · corrigé" if corrected else ""))
        t.setStyleSheet(f"background:transparent; color:{self.th.mut}; font-family:{FONT}; font-size:{int(10 * self.s)}px; letter-spacing:1px;")
        lay.addWidget(t)
        line = QHBoxLayout()
        line.setSpacing(int(6 * self.s))
        line.addWidget(icon_label(icon, int(18 * self.s)))
        v = QLabel(value)
        v.setStyleSheet(f"background:transparent; color:{value_color}; font-family:{FONT}; font-size:{int(17 * self.s)}px; font-weight:700;")
        line.addWidget(v)
        line.addStretch()
        lay.addLayout(line)
        return b

    def _set_thumb(self):
        pm = None
        if self._icon_override:
            pm = skin_pixmap(self._icon_override, self._thumb_size - 12)
        elif self.r.npc_id:
            pm = self._thumbs.get(pnj_data.npc_image_rel(self.r.npc_id), self._thumb_size)
        elif self.r.kind == "zaap":
            pm = skin_pixmap(ICON_ZAAP, self._thumb_size - 16)
        if pm is None or pm.isNull():  # image de repli (PNJ sans vignette, ou pas encore téléchargée)
            pm = skin_pixmap("icon_dofusteam.png", self._thumb_size - 20)
        self.thumb.setPixmap(pm)

    def refresh_thumb(self, rel):
        if self.r.npc_id and rel == pnj_data.npc_image_rel(self.r.npc_id):
            self._set_thumb()

    def set_selected(self, on: bool):
        th = self.th
        self.setStyleSheet(f"QFrame#PnjCard{{background:{th.bg2}; border:1px solid {th.acc if on else th.border}; "
                           f"border-radius:{int(12 * getattr(self, 's', 1))}px;}}")

    def set_copied(self, done: bool):
        self.btn.setText("Copié" if done else self.btn.text())

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.selected.emit(self.r)
            self.copy_requested.emit(self.r)
        elif e.button() == Qt.MouseButton.RightButton:
            self.menu_requested.emit(self.r, e.globalPosition().toPoint())


COMPACT_TILE_W = 86      # largeur d'une tuile du mode discret (à l'échelle 1)


class CompactTile(QFrame):
    """Tuile discrète d'un PNJ (mode pack) : son icône, sa position dessous. Clic = copier la commande."""
    copy_requested = pyqtSignal(object)
    menu_requested = pyqtSignal(object, object)

    def __init__(self, r: Result, th: Theme, s: float, thumbs: Thumbs, cmd: str, tip: str, corrected=False,
                 no_position=False, label_override="", parent=None):
        super().__init__(parent)
        self.r, self.th, self.no_position = r, th, no_position
        self.setCursor(Qt.CursorShape.ArrowCursor if no_position else Qt.CursorShape.PointingHandCursor)
        self.setToolTip(tip)
        self.setObjectName("CompactTile")
        self.setFixedWidth(int(COMPACT_TILE_W * s))
        self._style(False)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(int(5 * s), int(5 * s), int(5 * s), int(4 * s))
        lay.setSpacing(int(2 * s))
        self._size = int(44 * s)
        self._thumbs = thumbs
        pic = QLabel()
        pic.setFixedSize(self._size, self._size)
        pic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pic.setStyleSheet(f"background:{th.bg3}; border:none; border-radius:{int(8 * s)}px;")
        pm = thumbs.get(pnj_data.npc_image_rel(r.npc_id), self._size) if r.npc_id else None
        pic.setPixmap(pm if pm and not pm.isNull() else skin_pixmap("icon_dofusteam.png", self._size - 12))
        self._pic = pic
        lay.addWidget(pic, 0, Qt.AlignmentFlag.AlignHCenter)
        name = QLabel(r.name)
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name.setWordWrap(True)
        name.setStyleSheet(f"background:transparent; border:none; color:{th.text}; font-family:{FONT}; font-size:{int(10 * s)}px; font-weight:600;")
        lay.addWidget(name)
        text = label_override or f"{r.x},{r.y}" + ("*" if corrected else "")
        pos = QLabel(text)
        pos.setAlignment(Qt.AlignmentFlag.AlignCenter)
        color = th.mut if no_position else th.acc
        pos.setStyleSheet(f"background:transparent; border:none; color:{color}; font-family:{FONT}; "
                          f"font-size:{int(11 * s)}px; font-weight:700;")
        lay.addWidget(pos)

    def _style(self, on):
        th = self.th
        self.setStyleSheet(f"QFrame#CompactTile{{background:{th.bg2}; border:1px solid {th.acc if on else th.border}; border-radius:10px;}}"
                           + ("" if self.no_position else f"QFrame#CompactTile:hover{{border-color:{th.acc};}}"))

    def flash(self):
        """Retour visuel d'une copie (la fenêtre est trop petite pour un message)."""
        self._style(True)
        QTimer.singleShot(700, lambda: self._style(False))

    def refresh_thumb(self, rel):
        if self.r.npc_id and rel == pnj_data.npc_image_rel(self.r.npc_id):
            pm = self._thumbs.get(rel, self._size)
            if pm and not pm.isNull():
                self._pic.setPixmap(pm)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and not self.no_position:
            self.copy_requested.emit(self.r)
        elif e.button() == Qt.MouseButton.RightButton:
            self.menu_requested.emit(self.r, e.globalPosition().toPoint())


# ── Grille adaptative : 1 à N colonnes selon la largeur ─────────────────────────
class CardGrid(QWidget):
    def __init__(self, min_col=330, gap=10, center=False, parent=None):
        super().__init__(parent)
        self.min_col, self.gap, self.center = min_col, gap, center
        self._items: list = []
        self._cols = 0
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(gap)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

    def set_items(self, items):
        for w in self._items:
            self.grid.removeWidget(w)
            w.hide(); w.setParent(None); w.deleteLater()
        self._items = list(items)
        self._place(force=True)

    def count(self):
        return len(self._items)

    def minimumSizeHint(self):
        # sans ça, la grille garde le nombre de colonnes d'une largeur passée et empêche la fenêtre de rétrécir
        return QSize(self.min_col, 0)

    def _cols_for(self, w):
        return max(1, (w + self.gap) // (self.min_col + self.gap))

    def _place(self, force=False):
        cols = self._cols_for(self.width())
        if not force and cols == self._cols:
            return
        self._cols = cols
        for w in self._items:
            self.grid.removeWidget(w)
        for i, w in enumerate(self._items):
            if self.center:
                self.grid.addWidget(w, i // cols, i % cols, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
            else:
                self.grid.addWidget(w, i // cols, i % cols)
        for c in range(cols):
            self.grid.setColumnStretch(c, 1)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._place()


# ── Dialogues ───────────────────────────────────────────────────────────────────
def _spin(lo=-99, hi=99, val=0):
    s = QSpinBox()
    s.setRange(lo, hi)
    s.setValue(val)
    s.setMinimumHeight(34)
    s.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return s


def _field(dlg, label, icon, *widgets):
    """Une ligne de formulaire : icône du jeu + libellé, puis les champs."""
    dlg.body.addWidget(dlg.section(label))
    row = QHBoxLayout()
    row.setSpacing(8)
    if icon:
        row.addWidget(icon_label(icon, 22))
    for w in widgets:
        row.addWidget(w, 1)
    dlg.body.addLayout(row)


class CorrectionDialog(DtDialog):
    """Corriger la position et/ou le zaap d'un PNJ (local uniquement). `reset` = retour à l'original."""

    def __init__(self, r: Result, th: Theme, parent=None):
        super().__init__(parent, "Corriger ce PNJ", f"{r.name} : position et zaap conseillé. Stocké sur ton PC uniquement.", width=420)
        self.reset = False
        self.x, self.y = _spin(val=r.x), _spin(val=r.y)
        _field(self, "Position (x, y)", ICON_POSITION, self.x, self.y)
        zx, zy = (r.zaap.x, r.zaap.y) if r.zaap else (r.x, r.y)
        self.zx, self.zy = _spin(val=zx), _spin(val=zy)
        _field(self, "Zaap conseillé (x, y)", ICON_ZAAP, self.zx, self.zy)
        self.add_button("Revenir à l'original", "ghost", lambda: (setattr(self, "reset", True), self.accept()), min_width=150)
        self.add_button("Annuler", "ghost", self.reject)
        self.add_button("Enregistrer", "primary", self.accept)
        self._r = r

    def result_correction(self):
        if self.reset:
            return None
        c = {}
        if (self.x.value(), self.y.value()) != (self._r.x, self._r.y):
            c.update(x=self.x.value(), y=self.y.value())
        cur = (self._r.zaap.x, self._r.zaap.y) if self._r.zaap else None
        if (self.zx.value(), self.zy.value()) != cur:
            c["zaap"] = [self.zx.value(), self.zy.value()]
        return c or None


class CustomPosDialog(DtDialog):
    """Position perso : nom, coordonnées, icône du jeu au choix."""

    def __init__(self, th: Theme, parent=None, pos=None):
        super().__init__(parent, "Position perso" if not pos else "Modifier la position", "Un endroit à toi : champ, atelier, banque…", width=420)
        self.name = QLineEdit(pos["name"] if pos else "")
        self.name.setPlaceholderText("Ex : Mon champ")
        self.name.setMinimumHeight(36)
        _field(self, "Nom", None, self.name)
        self.x, self.y = _spin(val=pos["x"] if pos else 0), _spin(val=pos["y"] if pos else 0)
        _field(self, "Position (x, y)", ICON_POSITION, self.x, self.y)
        self.icon = QComboBox()
        self.icon.setMinimumHeight(34)
        for label, f in CUSTOM_ICON_CHOICES:
            self.icon.addItem(label, f)
        if pos and pos.get("icon"):
            i = self.icon.findData(pos["icon"])
            if i >= 0:
                self.icon.setCurrentIndex(i)
        _field(self, "Icône", None, self.icon)
        self.add_button("Annuler", "ghost", self.reject)
        self.add_button("Enregistrer", "primary", self.accept)
        self.name.setFocus()

    def value(self):
        return {"name": self.name.text().strip() or "Position", "x": self.x.value(), "y": self.y.value(),
                "icon": self.icon.currentData()}
