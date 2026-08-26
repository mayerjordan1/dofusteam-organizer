"""Page "Rosters" — wrap plein-écran de RosterPanel (main.py).

Un roster = liste nommée et indépendante de persos (contrairement à l'ancien
système Team 1-4, un même perso peut appartenir à plusieurs rosters).
Appliquer un roster active ses membres et désactive les autres dans le cycle
(Tab, fermer team, etc.) via DofusLogic.apply_roster() — ne touche pas à
l'ordre d'initiative, qui reste géré par les Presets.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel


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
        s.setWordWrap(True)
        lay.addWidget(s)
    return header


class RostersPage(QWidget):
    """Page pleine largeur listant/éditant/appliquant les rosters.

    Le signal `roster_applied` de RosterPanel est ré-exposé tel quel pour que
    MainWindow puisse rafraîchir la mini-toolbar sans dépendance directe
    entre les deux pages.
    """

    def __init__(self, config, logic, parent=None):
        super().__init__(parent)
        self.config = config
        self.logic = logic
        self._build()

    def _build(self):
        from main import RosterPanel  # import tardif — évite le cycle pages<->main

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        lay.addWidget(_make_header(
            "Rosters",
            "Groupes de persos réutilisables — change d'activité en un clic sans retoucher tes 8 comptes un par un.",
        ))

        body = QWidget()
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(24, 18, 24, 18)
        body_lay.setSpacing(0)

        self.panel = RosterPanel(self.config, self.logic, body)
        body_lay.addWidget(self.panel)
        body_lay.addStretch()

        lay.addWidget(body)
        lay.addStretch()

        self.roster_applied = self.panel.roster_applied

    def refresh_rosters(self):
        self.panel.refresh_rosters()
