"""Page "Classes" — fiche de classe (pour l'instant : Huppermage).

Tableau des combinaisons élémentaires : quel effet obtenir, quelle paire
d'éléments il faut, et quels sorts enchaîner (3 PA chacun). Données statiques,
icônes tirées du jeu (skin/hm_*.png) ; aucune écriture dans la config.
"""
from PyQt6.QtWidgets import (
    QSizePolicy, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QScrollArea, QFrame,
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

from paths import SKIN_DIR
from theme import (
    BG, BG2, BG3, ACC, RED, GREEN, TEXT, MUT, BORDER, BORDER2, mono, section_label, card, make_avatar,
)

ELEM = {
    "feu":   ("Feu",   "#ff6a3d", "in.png"),
    "terre": ("Terre", "#b98a4a", "fo.png"),
    "air":   ("Air",   "#6dc96d", "ag.png"),
    "eau":   ("Eau",   "#4fa3e0", "ch.png"),
}

# clé -> (nom, élément, icône)
SPELLS = {
    "lf": ("Lance-flamme",  "feu",   "hm_lanceflamme.png"),
    "os": ("Onde Sismique", "terre", "hm_ondesismique.png"),
    "et": ("Éther",         "air",   "hm_ether.png"),
    "st": ("Stalagmite",    "eau",   "hm_stalagmite.png"),
    "de": ("Déflagration",  "feu",   "hm_deflagration.png"),
    "me": ("Météore",       "terre", "hm_meteore.png"),
    "av": ("Avalanche",     "eau",   "hm_avalanche.png"),
    "la": ("Lame Astrale",  "air",   "hm_laneastrale.png"),
}

BASE = [
    ("lf", "retire des PA"),
    ("os", "retire des PM"),
    ("et", "retire de la Portée"),
    ("st", "réduit les dommages finaux"),
]

# effet, icône effet, signe (-/+), combo (nom, icône), valeur, icône valeur,
# couleur valeur, note, sorts (a, b), variante (a, b)
ROWS = [
    ("Retrait PA",  "pa.png", "-", ("Carbonisation", "hm_combo_carbonisation.png"),
     "−2 PA", "pa.png", ACC, "Esquivables", ("lf", "et"), ("de", "la")),
    ("Retrait PM",  "pm.png", "-", ("Enlisement", "hm_combo_enlisement.png"),
     "−3 PM", "pm.png", ACC, "Esquivables", ("os", "st"), ("me", "av")),
    ("Retrait PO",  "hm_range.png", "-", ("Assèchement", "hm_combo_assechement.png"),
     "−3 PO", "hm_range.png", ACC, "Non esquivable", ("os", "et"), ("me", "la")),
    ("Retrait Fuite", "hm_escape.png", "-", ("Ébullition", "hm_combo_ebullition.png"),
     "−60 Fuite", "hm_escape.png", ACC, "", ("lf", "st"), ("de", "av")),
    ("Baisse des dégâts", "dmgRecus.png", "-", ("Cristallisation", "hm_combo_cristallisation.png"),
     "−15 %", "dmgRecus.png", RED, "Dommages infligés par la cible", ("st", "et"), ("av", "la")),
    ("Augmente les dégâts", "dmgRecus.png", "+", ("Éruption", "hm_combo_eruption.png"),
     "+15 %", "dmgRecus.png", RED, "Dommages subis par la cible", ("lf", "os"), ("de", "me")),
]

# Largeurs relatives des 4 colonnes (en-tête et lignes alignés dessus)
COLS = (20, 17, 15, 48)


def _pix(filename, size):
    p = QPixmap(str(SKIN_DIR / filename))
    if p.isNull():
        return None
    return p.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)


def _icon(filename, size, border=None, radius=8):
    """QLabel image ; `border` = couleur du contour (élément du sort)."""
    lb = QLabel()
    pix = _pix(filename, size)
    if pix:
        lb.setPixmap(pix)
    lb.setFixedSize(size, size)
    lb.setAlignment(Qt.AlignmentFlag.AlignCenter)
    if border:
        lb.setFixedSize(size + 4, size + 4)
        lb.setStyleSheet(f"background:transparent; border:2px solid {border}; border-radius:{radius}px;")
    else:
        lb.setStyleSheet("background:transparent; border:none;")
    return lb


def _text(txt, color=TEXT, size=12, bold=False, mono_font=False):
    lb = QLabel(txt)
    f = "font-family:'Space Mono';" if mono_font else ""
    lb.setStyleSheet(f"color:{color}; font-size:{size}px; font-weight:{700 if bold else 500}; background:transparent; border:none; {f}")
    return lb


def _make_header(title, subtitle):
    header = QWidget()
    header.setObjectName("PageHeader")
    lay = QVBoxLayout(header)
    lay.setContentsMargins(24, 18, 24, 14)
    lay.setSpacing(2)
    t = QLabel(title)
    t.setObjectName("PageTitle")
    lay.addWidget(t)
    s = QLabel(subtitle)
    s.setObjectName("PageSubtitle")
    s.setWordWrap(True)
    lay.addWidget(s)
    return header


class ClassesPage(QWidget):
    def __init__(self, config=None, logic=None, parent=None):
        super().__init__(parent)
        self.config = config
        self.logic = logic
        self._build()

    # ── Blocs ───────────────────────────────────────────────────────────────
    def _class_header(self):
        box = card(QWidget())
        lay = QHBoxLayout(box)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(14)

        av = QLabel()
        av.setFixedSize(64, 64)
        av.setStyleSheet(f"background:{BG3}; border:1px solid {BORDER2}; border-radius:32px;")
        av.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pm = make_avatar("Huppermage", 60)
        if pm:
            av.setPixmap(pm)
        lay.addWidget(av)

        col = QVBoxLayout()
        col.setSpacing(2)
        col.addWidget(_text("CLASSES", ACC, 10, True, True))
        t = _text("Huppermage", TEXT, 20, True, True)
        col.addWidget(t)
        sub = _text("Combinaisons élémentaires : associe deux éléments dans le même tour pour déclencher un effet sur la cible.", MUT, 12)
        sub.setWordWrap(True)
        col.addWidget(sub)
        lay.addLayout(col, 1)

        for key in ("feu", "terre", "air", "eau"):
            name, color, ico = ELEM[key]
            chip = QWidget()
            chip.setObjectName(f"Chip{key}")
            chip.setStyleSheet(f"QWidget#Chip{key} {{ background:{BG3}; border:1px solid {BORDER}; border-radius:14px; }}")
            cl = QHBoxLayout(chip)
            cl.setContentsMargins(6, 3, 10, 3)
            cl.setSpacing(5)
            cl.addWidget(_icon(ico, 18))
            cl.addWidget(_text(name, color, 11, True))
            lay.addWidget(chip)
        return box

    def _base_spells(self):
        wrap = QWidget()
        wl = QVBoxLayout(wrap)
        wl.setContentsMargins(0, 0, 0, 0)
        wl.setSpacing(8)
        wl.addWidget(section_label("Sorts de base · 3 PA · 3 lancers par tour"))
        row = QHBoxLayout()
        row.setSpacing(10)
        for key, effet in BASE:
            name, elem, ico = SPELLS[key]
            en, color, _ = ELEM[elem]
            c = card(QWidget())
            cl = QHBoxLayout(c)
            cl.setContentsMargins(10, 8, 12, 8)
            cl.setSpacing(10)
            cl.addWidget(_icon(ico, 40, color, 9))
            tl = QVBoxLayout()
            tl.setSpacing(0)
            tl.addWidget(_text(name, TEXT, 13, True))
            tl.addWidget(_text(f"Dégâts {en} · {effet}", MUT, 11))
            cl.addLayout(tl, 1)
            row.addWidget(c, 1)
        wl.addLayout(row)
        return wrap

    def _spell_chip(self, key, small=False):
        name, elem, ico = SPELLS[key]
        color = ELEM[elem][1]
        chip = QWidget()
        chip.setObjectName(f"SpChip{key}{int(small)}")
        chip.setStyleSheet(f"QWidget#{chip.objectName()} {{ background:{BG3}; border:1px solid {BORDER}; border-radius:9px; }}")
        cl = QHBoxLayout(chip)
        cl.setContentsMargins(3, 3, 8, 3)
        cl.setSpacing(6)
        cl.addWidget(_icon(ico, 22 if small else 30, color, 7))
        cl.addWidget(_text(name, MUT if small else TEXT, 11 if small else 12, not small))
        cl.addWidget(_text("3", MUT, 10, False, True))
        cl.addWidget(_icon("pa.png", 14))
        return chip

    def _pair(self, a, b, small=False, total=False):
        h = QHBoxLayout()
        h.setSpacing(6)
        h.addWidget(self._spell_chip(a, small))
        h.addWidget(_text("+", MUT, 13, False, True))
        h.addWidget(self._spell_chip(b, small))
        if total:
            h.addSpacing(4)
            h.addWidget(_text("= 6", ACC, 11, True, True))
            h.addWidget(_icon("pa.png", 14))
        h.addStretch()
        return h

    def _effect_cell(self, label, icon, sign):
        w = QWidget()
        w.setStyleSheet("background:transparent;")
        hl = QHBoxLayout(w)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(12)

        holder = QWidget()
        holder.setFixedSize(48, 46)
        holder.setStyleSheet("background:transparent;")
        box = QLabel(holder)
        box.setGeometry(0, 6, 40, 40)
        box.setStyleSheet(f"background:{BG3}; border:1px solid {BORDER2}; border-radius:10px;")
        box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pix = _pix(icon, 28)
        if pix:
            box.setPixmap(pix)
        badge = QLabel("−" if sign == "-" else "+", holder)
        badge.setGeometry(30, 0, 17, 17)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(f"background:{RED if sign == '-' else GREEN}; color:#0d1117; border-radius:8px; "
                            f"font-weight:700; font-size:12px; font-family:'Space Mono';")
        hl.addWidget(holder)
        lbl = _text(label, TEXT, 14, True)
        lbl.setWordWrap(True)
        hl.addWidget(lbl, 1)
        return w

    def _combo_cell(self, combo):
        name, ico = combo
        w = QWidget()
        w.setStyleSheet("background:transparent;")
        hl = QHBoxLayout(w)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(10)
        hl.addWidget(_icon(ico, 52))
        hl.addWidget(_text(name, TEXT, 13, True), 1)
        return w

    def _detail_cell(self, value, icon, color, note):
        w = QWidget()
        w.setStyleSheet("background:transparent;")
        vl = QVBoxLayout(w)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(2)
        top = QHBoxLayout()
        top.setSpacing(6)
        top.addWidget(_icon(icon, 20))
        top.addWidget(_text(value, color, 15, True, True))
        top.addStretch()
        vl.addLayout(top)
        if note:
            n = _text(note, MUT, 11)
            n.setWordWrap(True)
            vl.addWidget(n)
        return w

    def _spells_cell(self, pair, alt):
        w = QWidget()
        w.setStyleSheet("background:transparent;")
        vl = QVBoxLayout(w)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(6)
        vl.addLayout(self._pair(pair[0], pair[1], total=True))
        h = QHBoxLayout()
        h.setSpacing(6)
        h.addWidget(_text("ou", MUT, 11))
        h.addLayout(self._pair(alt[0], alt[1], small=True), 1)
        vl.addLayout(h)
        return w

    def _table(self):
        wrap = QWidget()
        wl = QVBoxLayout(wrap)
        wl.setContentsMargins(0, 0, 0, 0)
        wl.setSpacing(8)

        head = QHBoxLayout()
        head.setContentsMargins(14, 0, 14, 0)
        head.setSpacing(12)
        for i, t in enumerate(("Effet recherché", "Combinaison d'états", "Détail de l'effet", "Sorts à enchaîner")):
            lb = QLabel(t.upper())
            lb.setFont(mono(9, True))
            lb.setStyleSheet(f"color:{MUT}; letter-spacing:1.2px; background:transparent;")
            head.addWidget(lb, COLS[i])
        wl.addLayout(head)

        for (effet, eico, sign, combo, val, vico, vcol, note, pair, alt) in ROWS:
            row = card(QWidget())
            rl = QHBoxLayout(row)
            rl.setContentsMargins(14, 10, 14, 10)
            rl.setSpacing(12)
            cells = (self._effect_cell(effet, eico, sign), self._combo_cell(combo),
                     self._detail_cell(val, vico, vcol, note), self._spells_cell(pair, alt))
            for i, cell in enumerate(cells):
                # Ignored : la largeur vient du stretch seul, donc colonnes alignées d'une ligne à l'autre
                cell.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
                rl.addWidget(cell, COLS[i])
            wl.addWidget(row)

        hint = QLabel("Contour de chaque sort = son élément. Valeurs des effets (−2 PA, −3 PM…) à confirmer en jeu.")
        hint.setStyleSheet(f"color:{MUT}; font-size:11px;")
        hint.setWordWrap(True)
        wl.addWidget(hint)
        return wrap

    # ── Page ────────────────────────────────────────────────────────────────
    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(_make_header("Classes", "Fiches de classe : combinaisons, sorts clés et effets à connaître."))

        body = QWidget()
        bl = QVBoxLayout(body)
        bl.setContentsMargins(24, 10, 24, 18)
        bl.setSpacing(16)
        bl.addWidget(self._class_header())
        bl.addWidget(self._base_spells())
        bl.addWidget(self._table())
        bl.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background:transparent;")
        scroll.setWidget(body)
        lay.addWidget(scroll, 1)
