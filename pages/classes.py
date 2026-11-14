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
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(10)

        av = QLabel()
        av.setFixedSize(44, 44)
        av.setStyleSheet(f"background:{BG3}; border:1px solid {BORDER2}; border-radius:22px;")
        av.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pm = make_avatar("Huppermage", 40)
        if pm:
            av.setPixmap(pm)
        lay.addWidget(av)

        col = QVBoxLayout()
        col.setSpacing(2)
        col.addWidget(_text("CLASSES", ACC, 10, True, True))
        t = _text("Huppermage", TEXT, 16, True, True)
        col.addWidget(t)
        sub = _text("Combinaisons élémentaires : associe deux éléments dans le même tour pour déclencher un effet sur la cible.", MUT, 11)
        sub.setWordWrap(True)
        col.addWidget(sub)
        lay.addLayout(col, 1)

        for key in ("feu", "terre", "air", "eau"):
            name, color, ico = ELEM[key]
            chip = QWidget()
            chip.setObjectName(f"Chip{key}")
            chip.setStyleSheet(f"QWidget#Chip{key} {{ background:{BG3}; border:1px solid {BORDER}; border-radius:11px; }}")
            cl = QHBoxLayout(chip)
            cl.setContentsMargins(5, 2, 8, 2)
            cl.setSpacing(4)
            cl.addWidget(_icon(ico, 14))
            cl.addWidget(_text(name, color, 10, True))
            lay.addWidget(chip)
        return box

    def _base_spells(self):
        wrap = QWidget()
        wl = QVBoxLayout(wrap)
        wl.setContentsMargins(0, 0, 0, 0)
        wl.setSpacing(6)
        wl.addWidget(section_label("Sorts de base · 3 PA · 3 lancers par tour"))
        row = QHBoxLayout()
        row.setSpacing(8)
        for key, effet in BASE:
            name, elem, ico = SPELLS[key]
            en, color, _ = ELEM[elem]
            c = card(QWidget())
            cl = QHBoxLayout(c)
            cl.setContentsMargins(8, 5, 10, 5)
            cl.setSpacing(8)
            cl.addWidget(_icon(ico, 28, color, 7))
            tl = QVBoxLayout()
            tl.setSpacing(0)
            tl.addWidget(_text(name, TEXT, 12, True))
            tl.addWidget(_text(f"Dégâts {en} · {effet}", MUT, 10))
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
        cl.setContentsMargins(2, 2, 6, 2)
        cl.setSpacing(4)
        cl.addWidget(_icon(ico, 17 if small else 22, color, 6))
        cl.addWidget(_text(name, MUT if small else TEXT, 10 if small else 11, not small))
        cl.addWidget(_text("3", MUT, 9, False, True))
        cl.addWidget(_icon("pa.png", 11))
        return chip

    def _pair(self, a, b, small=False, total=False, center=False, lead=None, pad=0):
        """center : enchaînement centré. lead : widget (« ou ») placé juste avant ; pad : marge de même largeur de chaque
        côté, pour que le « ou » ne décale pas le centre de la ligne du bas par rapport à celle du haut."""
        h = QHBoxLayout()
        h.setSpacing(4)
        if center:
            h.addStretch()
        if lead is not None:
            h.addWidget(lead)
        elif pad:
            h.addSpacing(pad)
        h.addWidget(self._spell_chip(a, small))
        h.addWidget(_text("+", MUT, 11, False, True))
        h.addWidget(self._spell_chip(b, small))
        if total:
            h.addSpacing(4)
            h.addWidget(_text("= 6", ACC, 10, True, True))
            h.addWidget(_icon("pa.png", 11))
        if pad:
            h.addSpacing(pad)
        h.addStretch()
        return h

    def _effect_cell(self, label, icon, sign):
        w = QWidget()
        w.setStyleSheet("background:transparent;")
        hl = QHBoxLayout(w)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(8)

        holder = QWidget()
        holder.setFixedSize(36, 34)
        holder.setStyleSheet("background:transparent;")
        box = QLabel(holder)
        box.setGeometry(0, 4, 30, 30)
        box.setStyleSheet(f"background:{BG3}; border:1px solid {BORDER2}; border-radius:8px;")
        box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pix = _pix(icon, 20)
        if pix:
            box.setPixmap(pix)
        badge = QLabel("−" if sign == "-" else "+", holder)
        badge.setGeometry(22, 0, 14, 14)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(f"background:{RED if sign == '-' else GREEN}; color:#0d1117; border-radius:7px; "
                            f"font-weight:700; font-size:10px; font-family:'Space Mono';")
        hl.addWidget(holder)
        lbl = _text(label, TEXT, 12, True)
        lbl.setWordWrap(True)
        hl.addWidget(lbl, 1)
        return w

    def _combo_cell(self, combo):
        name, ico = combo
        w = QWidget()
        w.setStyleSheet("background:transparent;")
        hl = QHBoxLayout(w)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(8)
        hl.addWidget(_icon(ico, 36))
        hl.addWidget(_text(name, TEXT, 12, True), 1)
        return w

    def _detail_cell(self, value, icon, color, note):
        w = QWidget()
        w.setStyleSheet("background:transparent;")
        vl = QVBoxLayout(w)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(1)
        top = QHBoxLayout()
        top.setSpacing(5)
        top.addWidget(_icon(icon, 16))
        top.addWidget(_text(value, color, 13, True, True))
        top.addStretch()
        vl.addLayout(top)
        if note:
            n = _text(note, MUT, 10)
            n.setWordWrap(True)
            vl.addWidget(n)
        return w

    def _spells_cell(self, pair, alt):
        w = QWidget()
        w.setStyleSheet("background:transparent;")
        # Les deux enchaînements sont centrés l'un par rapport à l'autre : le « ou » est placé juste avant la ligne du bas,
        # et la ligne du haut a une marge de même largeur de chaque côté, donc leurs centres restent alignés.
        vl = QVBoxLayout(w)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(3)
        ow = 18
        ou = _text("ou", MUT, 10)
        ou.setFixedWidth(ow)
        ou.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vl.addLayout(self._pair(pair[0], pair[1], total=True, center=True, pad=ow))
        vl.addLayout(self._pair(alt[0], alt[1], small=True, center=True, lead=ou, pad=ow))
        return w

    def _table(self):
        wrap = QWidget()
        wl = QVBoxLayout(wrap)
        wl.setContentsMargins(0, 0, 0, 0)
        wl.setSpacing(5)

        head = QHBoxLayout()
        head.setContentsMargins(10, 0, 10, 0)
        head.setSpacing(8)
        for i, t in enumerate(("Effet recherché", "Combinaison d'états", "Détail de l'effet", "Sorts à enchaîner")):
            lb = QLabel(t.upper())
            lb.setFont(mono(9, True))
            lb.setStyleSheet(f"color:{MUT}; letter-spacing:1.2px; background:transparent;")
            head.addWidget(lb, COLS[i])
        wl.addLayout(head)

        for (effet, eico, sign, combo, val, vico, vcol, note, pair, alt) in ROWS:
            row = card(QWidget())
            rl = QHBoxLayout(row)
            rl.setContentsMargins(10, 5, 10, 5)
            rl.setSpacing(8)
            cells = (self._effect_cell(effet, eico, sign), self._combo_cell(combo),
                     self._detail_cell(val, vico, vcol, note), self._spells_cell(pair, alt))
            for i, cell in enumerate(cells):
                # Ignored : la largeur vient du stretch seul, donc colonnes alignées d'une ligne à l'autre
                cell.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
                rl.addWidget(cell, COLS[i])
            wl.addWidget(row)

        hint = QLabel("Contour de chaque sort = son élément. Valeurs des effets (−2 PA, −3 PM…) à confirmer en jeu.")
        hint.setStyleSheet(f"color:{MUT}; font-size:10px;")
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
        bl.setContentsMargins(20, 8, 20, 14)
        bl.setSpacing(10)
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
