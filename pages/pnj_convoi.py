"""Panneau « convoi » manuel : déplacer plusieurs personnages vers un PNJ, étape par étape.

À chaque étape, le panneau COPIE la commande dans le presse-papiers et met la fenêtre du personnage concerné au premier
plan ; tu colles (Ctrl+V) et tu valides toi-même. C'est la version pas à pas. La version automatique (un clic sur une tuile
du pack discret) est dans pnj_convoi_macro.py et complète la macro /zaap de l'Organizer.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QApplication, QCheckBox

from pages.pnj_widgets import FONT, Theme, icon_label, ICON_ZAAP
from pnj_engine import Result, convoi_steps


class ConvoiPanel(QWidget):
    def __init__(self, logic, config, prefs, th: Theme, scale: float, parent=None):
        super().__init__(parent)
        self.logic, self.config, self.prefs, self.th, self.s = logic, config, prefs, th, scale
        self.target: Result | None = None
        self.steps: list = []
        self.i = 0
        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(0, 0, 0, 0)
        self.lay.setSpacing(int(6 * scale))
        self.render()

    def set_target(self, r: Result):
        self.target = r
        self._plan()
        self.render()

    def _accounts(self):
        return {a["name"]: a["hwnd"] for a in self.logic.get_cycle_list()}

    def _plan(self):
        names = list(self._accounts())
        leader = self.config.get("leader_name", "") or ""
        self.steps = convoi_steps(self.target, names, leader, self.prefs["convoi"].get("anti_lag", True)) if self.target else []
        self.i = 0

    def _lbl(self, text, color, size, bold=False):
        l = QLabel(text)
        l.setWordWrap(True)
        l.setStyleSheet(f"background:transparent; color:{color}; font-family:{FONT}; font-size:{int(size * self.s)}px; "
                        f"font-weight:{700 if bold else 400};")
        return l

    def render(self):
        while self.lay.count():
            it = self.lay.takeAt(0)
            w_ = it.widget()
            if w_:
                w_.hide(); w_.setParent(None); w_.deleteLater()
        th = self.th
        head = QHBoxLayout()
        head.addWidget(icon_label("icon_group.png", int(18 * self.s)))
        head.addWidget(self._lbl("CONVOI", th.mut, 11), 1)
        w = QWidget()
        w.setLayout(head)
        self.lay.addWidget(w)
        if not self.target:
            self.lay.addWidget(self._lbl("Clic droit sur une carte → « Envoyer au convoi ».", th.mut, 12))
            return
        r = self.target
        self.lay.addWidget(self._lbl(f"Destination : {r.name}  ({r.x}, {r.y})", th.text, 13, True))
        if not self.steps:
            self.lay.addWidget(self._lbl("Aucun personnage actif. Fais un scan des fenêtres d'abord.", th.mut, 12))
            return
        for k, st in enumerate(self.steps):
            cur = k == self.i
            done = k < self.i
            who = f"{st['who']} — " if st["who"] else ""
            txt = f"{k + 1}. {who}{st['text']}"
            color = th.acc if cur else (th.ghost if done else th.text)
            row = QHBoxLayout()
            if st["label"] == "zaap":
                row.addWidget(icon_label(ICON_ZAAP, int(16 * self.s)))
            row.addWidget(self._lbl(("▶ " if cur else "") + txt, color, 12, cur), 1)
            rw = QWidget()
            rw.setLayout(row)
            self.lay.addWidget(rw)
        btns = QHBoxLayout()
        nxt = QPushButton("Étape suivante" if self.i < len(self.steps) else "Terminé")
        nxt.setEnabled(self.i < len(self.steps))
        nxt.setCursor(Qt.CursorShape.PointingHandCursor)
        nxt.setStyleSheet(f"QPushButton{{background:{th.acc}; color:{th.bg}; border:none; border-radius:8px; padding:6px 14px; "
                          f"font-family:{FONT}; font-size:{int(12 * self.s)}px; font-weight:700;}}"
                          f"QPushButton:disabled{{background:{th.bg3}; color:{th.mut};}}")
        nxt.clicked.connect(self.next_step)
        again = QPushButton("Recommencer")
        again.setStyleSheet(f"QPushButton{{background:{th.bg3}; color:{th.text}; border:1px solid {th.border}; border-radius:8px; padding:6px 12px; font-family:{FONT};}}")
        again.clicked.connect(lambda: (self._plan(), self.render()))
        btns.addWidget(nxt, 1)
        btns.addWidget(again)
        bw = QWidget()
        bw.setLayout(btns)
        self.lay.addWidget(bw)
        self.lay.addWidget(self._lbl("Colle (Ctrl+V) et valide toi-même dans la fenêtre du personnage.", th.mut, 11))

    def next_step(self):
        if self.i >= len(self.steps):
            return
        st = self.steps[self.i]
        if st["kind"] == "copy":
            QApplication.clipboard().setText(st["text"])           # on copie…
            hwnd = self._accounts().get(st["who"])
            if hwnd:
                self.logic.focus_window(hwnd)                      # …et on met la fenêtre en avant. Rien d'autre.
        self.i += 1
        self.render()
