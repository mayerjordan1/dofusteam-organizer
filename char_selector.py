"""
DofusTeam — char_selector.py
Sélecteur rectangulaire 3x3 : 8 persos + logo DofusTeam au centre
"""
import math
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from paths import SKIN_DIR
from theme import BG, BG2, BG3, ACC, TEXT, MUT, GOLD, make_avatar

CELL=110  # cell size px


class CharCell(QPushButton):
    """Cellule d'un personnage dans la grille."""
    def __init__(self, acc, is_current=False, parent=None):
        super().__init__(parent)
        self.acc = acc
        live = acc.get("hwnd") is not None
        self.setFixedSize(CELL, CELL)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        border_c = ACC if is_current else "rgba(255,255,255,0.08)"
        bg_c     = "rgba(255,138,30,0.10)" if is_current else BG2
        self.setStyleSheet(f"""
            QPushButton {{background:{bg_c};border:2px solid {border_c};border-radius:10px;}}
            QPushButton:hover {{background:rgba(255,138,30,0.15);border-color:{ACC};}}
        """)
        lay = QVBoxLayout(self); lay.setContentsMargins(6,8,6,4); lay.setSpacing(3)
        av = QLabel(); av.setAlignment(Qt.AlignmentFlag.AlignCenter); av.setFixedHeight(46)
        pix = make_avatar(acc.get("classe",""), 46)
        if pix: av.setPixmap(pix)
        else: av.setText("?"); av.setStyleSheet(f"color:{MUT};font-size:18px;")
        lay.addWidget(av)
        nl = QLabel(acc["name"][:9]); nl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nl.setStyleSheet(f"color:{ACC if is_current else TEXT};font-size:10px;font-weight:{'700' if is_current else '600'};background:transparent;")
        lay.addWidget(nl)
        dot = QLabel("● EN JEU" if live else "○"); dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dot.setStyleSheet(f"color:{'#3fb950' if live else MUT};font-size:8px;font-family:'Space Mono';background:transparent;")
        lay.addWidget(dot)


class LogoCell(QWidget):
    """Cellule centrale avec le logo DofusTeam."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(CELL, CELL)
        self.setStyleSheet(f"background:rgba(255,138,30,0.06);border:2px solid rgba(255,138,30,0.2);border-radius:10px;")
        lay = QVBoxLayout(self); lay.setContentsMargins(10,10,10,6); lay.setSpacing(4)
        logo = QLabel(); logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_path = SKIN_DIR/"logo.png"
        if logo_path.exists():
            pix = QPixmap(str(logo_path)).scaled(52,52,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)
            logo.setPixmap(pix)
        else:
            logo.setText("🥚"); logo.setStyleSheet(f"font-size:32px;")
        lay.addWidget(logo)
        lbl = QLabel("DofusTeam"); lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(f"color:{ACC};font-size:9px;font-family:'Space Mono';font-weight:700;background:transparent;")
        lay.addWidget(lbl)


class CharSelector(QWidget):
    """
    Sélecteur rectangulaire 3x3 :
    - Jusqu'à 8 personnages autour du logo central
    - Positions dans l'ordre : haut-gauche → haut-droite → milieu-gauche → (LOGO) → milieu-droite → bas-gauche → bas-droite
    """
    char_selected = pyqtSignal(str)

    # Positions dans la grille 3x3 (row, col) pour les 8 chars
    # Centre = (1,1) = logo
    POSITIONS = [(0,0),(0,1),(0,2),(1,0),(1,2),(2,0),(2,1),(2,2)]

    def __init__(self, parent=None):
        super().__init__(None,
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._accounts = []; self._current = None
        self._build()

    def _build(self):
        GAP = 8; PAD = 14
        total = CELL * 3 + GAP * 2 + PAD * 2
        self.setFixedSize(total + 4, total + 4)
        self.container = QWidget(self)
        self.container.setStyleSheet(f"QWidget{{background:{BG};border:1px solid rgba(255,138,30,0.3);border-radius:14px;}}")
        self.container.setGeometry(2, 2, total, total)
        lay = QVBoxLayout(self.container); lay.setContentsMargins(PAD, PAD, PAD, PAD); lay.setSpacing(4)

        # Close button
        close_row = QHBoxLayout(); close_row.setContentsMargins(0,0,0,4)
        close_row.addStretch()
        cls = QPushButton("✕"); cls.setFixedSize(20,20)
        cls.setStyleSheet(f"background:transparent;color:{MUT};border:none;font-size:11px;")
        cls.clicked.connect(self.hide); close_row.addWidget(cls)
        lay.addLayout(close_row)

        self.grid = QGridLayout(); self.grid.setSpacing(GAP)
        lay.addLayout(self.grid)

    def show_for(self, accounts, current_name=None):
        self._accounts = accounts[:8]; self._current = current_name
        self._rebuild()
        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width()-self.width())//2, (screen.height()-self.height())//2)
        self.show(); self.raise_(); self.activateWindow()

    def _rebuild(self):
        # Clear grid
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        # Center logo
        self.grid.addWidget(LogoCell(), 1, 1)

        # Characters in their positions
        for i, acc in enumerate(self._accounts):
            if i >= len(self.POSITIONS): break
            r, c = self.POSITIONS[i]
            cell = CharCell(acc, acc["name"] == self._current)
            cell.clicked.connect(lambda _, a=acc: self._select(a["name"]))
            self.grid.addWidget(cell, r, c)

    def _select(self, name):
        self.char_selected.emit(name); self.hide()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Escape: self.hide()
