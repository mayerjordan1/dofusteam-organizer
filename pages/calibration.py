"""Page "Calibration" — configure les positions cliquées par les automatisations
(havre-sac, zaap, chat) et montre, par personnage, ce qui est déjà calibré.

Avant cette page : la calibration n'était accessible que via la touche F4 ou
un lien enfoui dans "Automatisations de zaap" — rien n'affichait l'état actuel
des positions enregistrées. Réutilise CalibrationManager (calibrator.py) sans
réécriture, comme AutomatisationsZaapPage/FenetresScanPage le font déjà.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal, QTimer

from theme import TEXT, MUT, BG2, BG3, GREEN, RED, ACC, BORDER, section_label, card, accent_btn, ghost_btn, make_avatar


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


class _CharStatusRow(QFrame):
    recalibrate = pyqtSignal(str, str)  # (mode, nom)

    def __init__(self, name, classe, chat_ok, parent=None):
        super().__init__(parent)
        self.setObjectName("CharStatusRow")
        self.setStyleSheet(f"QFrame#CharStatusRow {{ background:{BG2}; border:1px solid {BORDER}; border-radius:8px; }}")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(10)

        av = QLabel()
        av.setFixedSize(26, 26)
        av.setStyleSheet("background:transparent;border:none;")
        pix = make_avatar(classe or "", 26)
        if pix:
            av.setPixmap(pix)
        lay.addWidget(av)

        name_lbl = QLabel(name)
        name_lbl.setStyleSheet(f"color:{TEXT}; font-size:12px; font-weight:600; background:transparent; border:none;")
        lay.addWidget(name_lbl)
        lay.addStretch()

        status = QLabel("✅ Chat calibré" if chat_ok else "❌ Chat non calibré")
        status.setStyleSheet(f"color:{GREEN if chat_ok else RED}; font-size:11px; font-weight:600; background:transparent; border:none;")
        lay.addWidget(status)

        recal = QPushButton("🎯 Recalibrer" if chat_ok else "🎯 Calibrer")
        recal.setStyleSheet(
            f"background:rgba(255,138,30,0.1);color:{ACC};border:1px solid rgba(255,138,30,0.25);"
            f"border-radius:5px;padding:3px 10px;font-size:11px;font-weight:700;"
        )
        recal.clicked.connect(lambda _: self.recalibrate.emit("chat_multi", name))
        lay.addWidget(recal)

    def flash_ok(self):
        self.setStyleSheet(
            f"QFrame#CharStatusRow {{ background:rgba(63,185,80,0.18); border:1px solid {GREEN}; border-radius:8px; }}"
        )
        QTimer.singleShot(1200, lambda: self.setStyleSheet(
            f"QFrame#CharStatusRow {{ background:{BG2}; border:1px solid {BORDER}; border-radius:8px; }}"
        ))


class CalibrationPage(QWidget):
    """Page pleine largeur — statut de calibration par personnage + lancement
    des calibrations chat (chef, et 3.7 par personnage). La calibration
    Havre-sac + Zaap (ancien flow de téléportation, remplacé par /zaap) n'a
    plus de bouton ici — CalibrationManager mode "zaap" reste dans
    calibrator.py, dormant, pour l'ancien flow gardé en fallback."""

    open_calibration = pyqtSignal(str, str)  # mode, nom du personnage cible ("" = tous)

    def __init__(self, config, logic, parent=None):
        super().__init__(parent)
        self.config = config
        self.logic = logic
        self._build()
        self.refresh()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        lay.addWidget(_make_header(
            "Calibration",
            "Enregistre la position de la barre de chat — une fois sur le chef, et une fois par personnage pour /zaap.",
        ))

        body = QWidget()
        body_lay = QHBoxLayout(body)
        body_lay.setContentsMargins(24, 18, 24, 18)
        body_lay.setSpacing(16)

        body_lay.addWidget(self._build_list(), stretch=1)
        body_lay.addWidget(self._build_side(), stretch=0)

        lay.addWidget(body, stretch=1)

    def _build_list(self):
        panel = card(QWidget())
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(10)

        lay.addWidget(section_label("Personnages"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        container = QWidget()
        self.rows_lay = QVBoxLayout(container)
        self.rows_lay.setContentsMargins(0, 0, 0, 0)
        self.rows_lay.setSpacing(6)
        self.rows_lay.addStretch()
        scroll.setWidget(container)
        lay.addWidget(scroll, stretch=1)

        return panel

    def _build_side(self):
        side = card(QWidget())
        side.setFixedWidth(240)
        lay = QVBoxLayout(side)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)

        lay.addWidget(section_label("Chat (chef)"))
        desc2 = QLabel("Calibre une seule fois, sur le chef de groupe — utilisé pour l'invitation groupée.")
        desc2.setWordWrap(True)
        desc2.setStyleSheet(f"color:{MUT}; font-size:11px; background:transparent;")
        lay.addWidget(desc2)
        lay.addWidget(ghost_btn("💬 Calibrer le chat", lambda: self.open_calibration.emit("chat", "")))

        lay.addSpacing(10)
        lay.addWidget(section_label("Chat (3.7 — par personnage)"))
        desc3 = QLabel("À calibrer sur CHAQUE personnage — nécessaire pour /zaap, collé dans toutes les fenêtres.")
        desc3.setWordWrap(True)
        desc3.setStyleSheet(f"color:{MUT}; font-size:11px; background:transparent;")
        lay.addWidget(desc3)
        lay.addWidget(accent_btn("💬 Calibrer le chat (tous)", lambda: self.open_calibration.emit("chat_multi", "")))

        lay.addStretch()

        self.status_lbl = QLabel("—")
        self.status_lbl.setWordWrap(True)
        self.status_lbl.setStyleSheet(f"color:{MUT}; font-size:11px; background:transparent;")
        lay.addWidget(self.status_lbl)

        return side

    def refresh(self, just_calibrated=""):
        while self.rows_lay.count():
            item = self.rows_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        order = self.config.get("custom_order", [])
        classes = self.config.get("classes", {})
        macro_pos = self.config.get("macro_positions", {})
        chat_positions = macro_pos.get("chat_positions", {})

        if not order:
            empty = QLabel("Aucun compte — scanne d'abord depuis « Fenêtres & scan ».")
            empty.setStyleSheet(f"color:{MUT}; font-size:11px; background:transparent;")
            self.rows_lay.addWidget(empty)
        else:
            for name in order:
                row = _CharStatusRow(name, classes.get(name, ""), name in chat_positions)
                row.recalibrate.connect(lambda mode, n: self.open_calibration.emit(mode, n))
                self.rows_lay.addWidget(row)
                if name == just_calibrated:
                    row.flash_ok()
        self.rows_lay.addStretch()

        chat_multi_ok = len([n for n in order if n in chat_positions])
        chat_ok = bool(macro_pos.get("chat_position"))
        self.status_lbl.setText(
            f"Chat (chef) : {'✅ calibré' if chat_ok else '❌ non calibré'}\n"
            f"Chat 3.7 (par perso) : {chat_multi_ok}/{len(order)} calibré(s)"
        )
