"""Page "Mes équipes" — presets rapides, ordre d'initiative, actions de fenêtre.

Réutilise la logique métier existante (DofusLogic.apply_preset/sort_taskbar,
ScanThread, PresetEditor, InviteDialog) sans réécriture — cette page assemble
des widgets autour d'elle, tout le calcul reste dans main.py/dofus_logic.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QFrame,
)
from PyQt6.QtCore import Qt

from theme import TEXT, MUT, BG2, BG3, ACC, BORDER, section_label, card, accent_btn, ghost_btn, make_avatar

MAX_SLOTS = 8


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


class TeamSlotCard(QFrame):
    """Carte compacte horizontale = une position dans l'ordre d'initiative
    (config["custom_order"]). Volontairement distincte de AccountRow (qui
    reste la ligne détaillée avec actions ▲▼/leader/suppr) — ici juste un
    aperçu compact position + avatar + nom, pensé pour tenir en ligne."""

    def __init__(self, name, classe, pos_num, parent=None):
        super().__init__(parent)
        self.setFixedSize(96, 76)
        self.setStyleSheet(
            f"QFrame {{ background:{BG2}; border:1px solid {BORDER}; border-radius:8px; }}"
        )
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 6)
        lay.setSpacing(4)

        top = QHBoxLayout()
        top.setSpacing(4)
        pos_lbl = QLabel(str(pos_num))
        pos_lbl.setStyleSheet(f"color:{ACC}; font-weight:700; font-size:11px; background:transparent;")
        top.addWidget(pos_lbl)
        top.addStretch()
        lay.addLayout(top)

        av = QLabel()
        av.setFixedSize(32, 32)
        av.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pix = make_avatar(classe or "", 30)
        if pix:
            av.setPixmap(pix)
        else:
            av.setText("?")
            av.setStyleSheet(f"color:{MUT}; background:{BG3}; border-radius:16px;")
        av_row = QHBoxLayout()
        av_row.addStretch()
        av_row.addWidget(av)
        av_row.addStretch()
        lay.addLayout(av_row)

        name_lbl = QLabel()
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_lbl.setStyleSheet(f"color:{TEXT}; font-size:10px; font-weight:600; background:transparent;")
        fm = name_lbl.fontMetrics()
        name_lbl.setText(fm.elidedText(name, Qt.TextElideMode.ElideRight, 78))
        lay.addWidget(name_lbl)


class _EmptySlot(QFrame):
    def __init__(self, pos_num, parent=None):
        super().__init__(parent)
        self.setFixedSize(96, 76)
        self.setStyleSheet(
            f"QFrame {{ background:transparent; border:1px dashed {BORDER}; border-radius:8px; }}"
        )
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl = QLabel(str(pos_num))
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(f"color:{MUT}; font-size:11px; background:transparent;")
        lay.addWidget(lbl)


class _PresetPill(QPushButton):
    def __init__(self, name, count, parent=None):
        super().__init__(f"{name}  ·  {count}", parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(
            f"QPushButton {{ background:{BG3}; color:{MUT}; border:1px solid {BORDER};"
            f"border-radius:14px; padding:6px 14px; font-size:11.5px; font-weight:600; }}"
            f"QPushButton:hover {{ background:rgba(255,138,30,0.14); color:{ACC}; border-color:{ACC}; }}"
        )


class MesEquipesPage(QWidget):
    """Page principale — presets rapides + ordre d'initiative + actions de fenêtre."""

    def __init__(self, config, logic, parent=None):
        super().__init__(parent)
        self.config = config
        self.logic = logic
        self._scan_thread = None
        self._build()
        self.refresh()

    # ── construction ────────────────────────────────────────────────────
    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        lay.addWidget(_make_header(
            "Mes équipes",
            "Applique un preset, vérifie l'ordre d'initiative et gère tes fenêtres Dofus.",
        ))

        body = QWidget()
        body_lay = QHBoxLayout(body)
        body_lay.setContentsMargins(24, 18, 24, 18)
        body_lay.setSpacing(16)

        body_lay.addWidget(self._build_left(), stretch=1)
        body_lay.addWidget(self._build_right(), stretch=0)

        lay.addWidget(body, stretch=1)

    def _build_left(self):
        left = QWidget()
        llay = QVBoxLayout(left)
        llay.setContentsMargins(0, 0, 0, 0)
        llay.setSpacing(18)

        # Presets compacts en onglets (pills horizontales)
        llay.addWidget(section_label("Presets"))
        pills_scroll = QScrollArea()
        pills_scroll.setWidgetResizable(True)
        pills_scroll.setFixedHeight(46)
        pills_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        pills_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        pills_container = QWidget()
        self.pills_lay = QHBoxLayout(pills_container)
        self.pills_lay.setContentsMargins(2, 2, 2, 2)
        self.pills_lay.setSpacing(8)
        pills_scroll.setWidget(pills_container)
        llay.addWidget(pills_scroll)

        # Ordre d'initiative
        order_header = QHBoxLayout()
        order_header.addWidget(section_label("Ordre d'initiative"))
        order_header.addStretch()
        order_header.addWidget(ghost_btn("✏ Modifier l'ordre", self._edit_order))
        llay.addLayout(order_header)

        slots_scroll = QScrollArea()
        slots_scroll.setWidgetResizable(True)
        slots_scroll.setFixedHeight(96)
        slots_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        slots_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        slots_container = QWidget()
        self.slots_lay = QHBoxLayout(slots_container)
        self.slots_lay.setContentsMargins(2, 2, 2, 2)
        self.slots_lay.setSpacing(8)
        slots_scroll.setWidget(slots_container)
        llay.addWidget(slots_scroll)

        llay.addStretch()
        return left

    def _build_right(self):
        right = card(QWidget())
        right.setFixedWidth(220)
        rlay = QVBoxLayout(right)
        rlay.setContentsMargins(16, 16, 16, 16)
        rlay.setSpacing(10)

        rlay.addWidget(section_label("Fenêtres"))
        rlay.addWidget(ghost_btn("🔍 Scanner les fenêtres", self._scan))
        rlay.addWidget(ghost_btn("📊 Trier la barre Windows", self._sort_taskbar))

        rlay.addSpacing(6)
        rlay.addWidget(section_label("Groupe"))
        rlay.addWidget(accent_btn("👥 Invitation de groupe", self._open_invite))

        rlay.addStretch()

        self.status_lbl = QLabel("—")
        self.status_lbl.setWordWrap(True)
        self.status_lbl.setStyleSheet(f"color:{MUT}; font-size:11px; background:transparent;")
        rlay.addWidget(self.status_lbl)

        return right

    # ── rafraîchissement ────────────────────────────────────────────────
    def refresh(self):
        self._refresh_pills()
        self._refresh_slots()
        self._refresh_status()

    def _refresh_pills(self):
        while self.pills_lay.count():
            item = self.pills_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        presets = self.config.get("presets", [])
        if not presets:
            empty = QLabel("Aucun preset — crée-en un via « Modifier l'ordre ».")
            empty.setStyleSheet(f"color:{MUT}; font-size:11px; background:transparent;")
            self.pills_lay.addWidget(empty)
        else:
            for p in presets:
                pill = _PresetPill(p.get("name", "?"), len(p.get("order", [])))
                pill.clicked.connect(lambda _, pp=p: self._apply_preset(pp))
                self.pills_lay.addWidget(pill)
        self.pills_lay.addStretch()

    def _refresh_slots(self):
        while self.slots_lay.count():
            item = self.slots_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        order = self.config.get("custom_order", [])
        classes = self.config.get("classes", {})
        for i in range(MAX_SLOTS):
            if i < len(order):
                name = order[i]
                self.slots_lay.addWidget(TeamSlotCard(name, classes.get(name, ""), i + 1))
            else:
                self.slots_lay.addWidget(_EmptySlot(i + 1))
        self.slots_lay.addStretch()

    def _refresh_status(self):
        order = self.config.get("custom_order", [])
        live = len([a for a in (self.logic.all_accounts or []) if a.get("hwnd")])
        self.status_lbl.setText(f"{len(order)} compte(s) configuré(s) · {live} fenêtre(s) détectée(s)")

    # ── actions ─────────────────────────────────────────────────────────
    def _apply_preset(self, preset):
        self.logic.apply_preset(preset.get("order", []))
        self.refresh()

    def _edit_order(self):
        from main import PresetEditor  # import tardif — évite le cycle pages<->main
        editor = PresetEditor(self.config, -1, self)
        editor.saved.connect(self.refresh)
        editor.exec()

    def _scan(self):
        from main import ScanThread  # import tardif — évite le cycle pages<->main
        self.status_lbl.setText("Scan en cours…")

        def on_done(accounts):
            lv = len(accounts)
            if lv > 0:
                self.status_lbl.setText(f"✅  {lv} fenêtre(s) Dofus détectée(s)")
            else:
                self.status_lbl.setText("⚠  Aucune fenêtre Dofus — Dofus est-il ouvert ?")
            self.refresh()

        self._scan_thread = ScanThread(self.logic)
        self._scan_thread.done.connect(on_done)
        self._scan_thread.start()

    def _sort_taskbar(self):
        self.logic.sort_taskbar()

    def _open_invite(self):
        from invite_dialog import InviteDialog  # import tardif — évite le cycle pages<->main
        InviteDialog(self.config, self.logic, self).exec()
