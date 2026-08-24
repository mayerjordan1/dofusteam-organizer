"""Page "Chasse au trésor" — lanceur vers HuntDialog existant.

Décision du plan : hunt.py reste tel quel (QDialog autonome, données
DofusDB, recherche d'indices/zaaps), ouvert en modal depuis cette page
plutôt que réécrit/embarqué — la fenêtre a une taille fixe pensée pour
un usage ponctuel, pas pour vivre dans le QStackedWidget principal.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

from theme import MUT, section_label, card, accent_btn


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


class ChasseTresorPage(QWidget):
    """Page lanceur — ouvre HuntDialog (résolution d'indices via DofusDB)."""

    def __init__(self, config, logic, parent=None):
        super().__init__(parent)
        self.config = config
        self.logic = logic
        self._dialog = None
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        lay.addWidget(_make_header(
            "Chasse au trésor",
            "Résolution d'indices et recherche de zaaps via DofusDB.",
        ))

        body = QWidget()
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(24, 18, 24, 18)
        body_lay.setSpacing(12)

        panel = card(QWidget())
        panel.setFixedWidth(360)
        panel_lay = QVBoxLayout(panel)
        panel_lay.setContentsMargins(16, 16, 16, 16)
        panel_lay.setSpacing(10)

        panel_lay.addWidget(section_label("Outil de chasse"))
        desc = QLabel("Ouvre l'assistant de résolution d'indices (position, direction, zaap le plus proche).")
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color:{MUT}; font-size:11px; background:transparent;")
        panel_lay.addWidget(desc)
        panel_lay.addWidget(accent_btn("🗺  Ouvrir la chasse au trésor", self._open))

        body_lay.addWidget(panel)
        body_lay.addStretch()

        lay.addWidget(body)
        lay.addStretch()

    def _open(self):
        from hunt import HuntDialog  # import tardif — évite le cycle pages<->main
        self._dialog = HuntDialog(self.config, self.logic, self)
        self._dialog.exec()
