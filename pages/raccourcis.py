"""Page "Raccourcis clavier" — grille de tuiles (icône + action + touche).

Avant : cette grille de 10 bindings vivait dans _mk_shortcuts_bar (main.py),
une bande fixe entre le corps principal et la barre de statut. Ici, même
logique métier (aucune réécriture — juste config.get/set/save sur les mêmes
clés), déplacée dans une page dédiée pleine largeur et présentée en tuiles.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit, QPushButton,
)
from PyQt6.QtCore import Qt

from theme import MUT, TEXT, ACC, BG, section_label, card


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


DEFS = [
    ("Précédent", "prev_key", "⏮"), ("Suivant", "next_key", "⏭"), ("Rafraîchir", "refresh_key", "🔄"),
    ("Chef", "leader_key", "★"), ("Afficher/Cacher", "toggle_app_key", "👁"), ("Havre-sac", "game_haven_key", "🏠"),
    ("Sélecteur", "selector_key", "🎯"), ("Calibrer", "calib_key", "🎚"), ("Inviter", "invite_group_key", "👥"),
    ("Coller+Valider", "paste_active_key", "📋"),
]


class RaccourcisPage(QWidget):
    """Page pleine largeur listant/éditant les 10 raccourcis clavier, en tuiles."""

    def __init__(self, config, logic=None, parent=None):
        super().__init__(parent)
        self.config = config
        self._sc = {}
        self._build()

    def _tile(self, label, key, icon):
        t = card(QWidget())
        t.setFixedSize(152, 112)
        lay = QVBoxLayout(t)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(6)

        top = QHBoxLayout()
        top.setSpacing(0)
        ic = QLabel(icon)
        ic.setStyleSheet("font-size:18px;background:transparent;")
        top.addWidget(ic)
        top.addStretch()
        rm = QPushButton("✕")
        rm.setFixedSize(16, 16)
        rm.setToolTip("Effacer ce raccourci")
        rm.setStyleSheet(f"background:transparent;color:{MUT};border:none;font-size:9px;")
        top.addWidget(rm)
        lay.addLayout(top)

        lb = QLabel(label)
        lb.setStyleSheet(f"color:{TEXT};font-size:11px;font-weight:600;background:transparent;")
        lb.setWordWrap(True)
        lay.addWidget(lb, stretch=1)

        inp = QLineEdit(self.config.get(key, ""))
        inp.setFixedHeight(26)
        inp.setAlignment(Qt.AlignmentFlag.AlignCenter)
        inp.setPlaceholderText("—")
        inp.setStyleSheet(
            f"background:{BG};border:1px solid rgba(255,255,255,0.08);border-radius:5px;"
            f"padding:2px 6px;font-size:11px;color:{ACC};font-family:'Space Mono';font-weight:700;"
        )
        inp.textChanged.connect(lambda text, k=key: (self.config.set(k, text), self.config.save()))
        rm.clicked.connect(inp.clear)
        lay.addWidget(inp)

        self._sc[key] = inp
        return t

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        lay.addWidget(_make_header(
            "Raccourcis clavier",
            "Touches globales — précédent, suivant, chef, calibrer, inviter...",
        ))

        body = QWidget()
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(24, 18, 24, 18)
        body_lay.setSpacing(10)

        body_lay.addWidget(section_label("Raccourcis clavier"))

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)
        cols = 5
        for i, (label, key, icon) in enumerate(DEFS):
            r, c = divmod(i, cols)
            grid.addWidget(self._tile(label, key, icon), r, c)
        body_lay.addLayout(grid)
        body_lay.addStretch()

        lay.addWidget(body)
        lay.addStretch()
