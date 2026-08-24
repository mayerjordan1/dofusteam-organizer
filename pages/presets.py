"""Page "Presets d'initiative" — wrap plein-écran de PresetPanel existant.

Avant : PresetPanel vivait dans une card latérale (QScrollArea plafonnée à
160px de haut) au sein de la colonne droite de MainWindow. Ici, même
composant/logique (aucune réécriture métier), juste replacé en page pleine
largeur avec un header standard et sans le plafond de hauteur.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

from theme import MUT


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


class PresetsPage(QWidget):
    """Page pleine largeur listant/éditant les presets d'initiative.

    Le signal `preset_applied` de PresetPanel est ré-exposé tel quel pour
    que MainWindow puisse rafraîchir la page Mes équipes sans dépendance
    directe entre les deux pages.
    """

    def __init__(self, config, logic, parent=None):
        super().__init__(parent)
        self.config = config
        self.logic = logic
        self._build()

    def _build(self):
        from main import PresetPanel  # import tardif — évite le cycle pages<->main

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        lay.addWidget(_make_header(
            "Presets d'initiative",
            "Ordres de personnages réutilisables, applicables en un clic à n'importe quelle team.",
        ))

        body = QWidget()
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(24, 18, 24, 18)
        body_lay.setSpacing(0)

        self.panel = PresetPanel(self.config, self.logic, body)
        # Contrainte de 160px pensée pour une card latérale — retirée pour
        # laisser le panneau respirer sur toute la hauteur de la page.
        self.panel.scroll.setMaximumHeight(16777215)
        body_lay.addWidget(self.panel)
        body_lay.addStretch()

        lay.addWidget(body)
        lay.addStretch()

        self.preset_applied = self.panel.preset_applied

    def refresh_presets(self):
        self.panel.refresh_presets()
