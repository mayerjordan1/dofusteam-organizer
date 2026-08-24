"""Page "Raccourcis clavier" — wrap plein-écran de la grille existante.

Avant : cette grille de 10 bindings vivait dans _mk_shortcuts_bar (main.py),
une bande fixe entre le corps principal et la barre de statut. Ici, même
structure/logique (aucune réécriture métier — juste config.get/set/save
sur les mêmes clés), déplacée dans une page dédiée pleine largeur.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QLineEdit, QPushButton

from theme import MUT, ACC, BG, section_label, mono


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
    ("Précédent", "prev_key"), ("Suivant", "next_key"), ("Rafraîchir", "refresh_key"),
    ("Chef", "leader_key"), ("Afficher/Cacher", "toggle_app_key"), ("Havre-sac", "game_haven_key"),
    ("Sélecteur", "selector_key"), ("Calibrer", "calib_key"), ("Inviter", "invite_group_key"),
    ("Coller+Valider", "paste_active_key"),
]


class RaccourcisPage(QWidget):
    """Page pleine largeur listant/éditant les 10 raccourcis clavier."""

    def __init__(self, config, logic=None, parent=None):
        super().__init__(parent)
        self.config = config
        self._sc = {}
        self._build()

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
        body_lay.setSpacing(8)

        body_lay.addWidget(section_label("RACCOURCIS CLAVIER"))
        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(10)
        for i, (label, key) in enumerate(DEFS):
            r, c = divmod(i, 3)
            lb = QLabel(label.upper())
            lb.setFont(mono(8))
            lb.setStyleSheet(f"color:{MUT};letter-spacing:0.5px;")
            grid.addWidget(lb, r, c * 3)
            inp = QLineEdit(self.config.get(key, ""))
            inp.setFixedWidth(90)
            inp.setFixedHeight(28)
            inp.setStyleSheet(
                f"background:{BG};border:1px solid rgba(255,255,255,0.07);border-radius:5px;"
                f"padding:2px 6px;font-size:11px;color:{ACC};font-family:'Space Mono';"
            )
            inp.textChanged.connect(lambda t, k=key: (self.config.set(k, t), self.config.save()))
            grid.addWidget(inp, r, c * 3 + 1)
            rm = QPushButton("✕")
            rm.setFixedSize(18, 18)
            rm.setStyleSheet(f"background:transparent;color:{MUT};border:none;font-size:9px;")
            rm.clicked.connect(inp.clear)
            grid.addWidget(rm, r, c * 3 + 2)
            self._sc[key] = inp
        body_lay.addLayout(grid)
        body_lay.addStretch()

        lay.addWidget(body)
        lay.addStretch()
