"""Page "Gestion" — scan des fenêtres Dofus, liste des comptes, branding
et actions rapides (spam clic, trier la barre Windows, fermer la team).

Réutilise la logique métier existante (DofusLogic.scan_slots/sort_taskbar/
close_all/set_leader/move_account, ScanThread, AccountRow, CLASSES) sans
réécriture — priorité V1 explicite de l'utilisateur ("organiser les
fenêtres"). preset_card (ex-_mk_side_panel) n'est PAS repris ici : il vit
désormais dans pages/presets.py.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QComboBox, QLineEdit, QMessageBox, QDialog,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap

import threading, time

from theme import (
    BG, BG2, BG3, ACC, RED, GREEN, GOLD, TEXT, MUT, BORDER, STYLE,
    section_label, card, accent_btn, ghost_btn,
)
from paths import SKIN_DIR

try:
    import pyautogui
    pyautogui.FAILSAFE = False
    PYAUTOGUI_OK = True
except ImportError:
    PYAUTOGUI_OK = False


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


class FenetresScanPage(QWidget):
    """Page pleine largeur — scan/liste des comptes + mode/version + actions rapides.

    `accounts_changed` est émis après chaque scan/ajout/suppression/déplacement,
    pour que MainWindow puisse rafraîchir la mini-toolbar (`self.mini._rebuild_char_icons`)
    sans dépendance directe entre cette page et main.py.
    """

    accounts_changed = pyqtSignal(list)

    def __init__(self, config, logic, parent=None):
        super().__init__(parent)
        self.config = config
        self.logic = logic
        self._scan_thread = None
        self._spam = False
        self._rows = {}
        self._build()
        self._refresh()

    # ── construction ────────────────────────────────────────────────────
    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        lay.addWidget(_make_header(
            "Gestion",
            "Scanne, organise et pilote toutes tes fenêtres Dofus.",
        ))

        body = QWidget()
        body_lay = QHBoxLayout(body)
        body_lay.setContentsMargins(24, 18, 24, 18)
        body_lay.setSpacing(16)

        body_lay.addWidget(self._build_accounts_panel(), stretch=1)
        body_lay.addWidget(self._build_side_panel(), stretch=0)

        lay.addWidget(body, stretch=1)

    def _build_accounts_panel(self):
        panel = card(QWidget())
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(10)

        # Titre+badge sur leur propre ligne, actions sur la suivante — évite que
        # ce header pousse la largeur minimale de la page au-delà de 700px
        # (les 2 boutons + le titre ne tenaient pas sur une seule ligne à la
        # largeur minimale du panneau).
        title_row = QHBoxLayout()
        title_row.addWidget(section_label("Comptes"))
        self.count_badge = QLabel("0")
        self.count_badge.setStyleSheet(
            f"color:{ACC}; background:rgba(255,138,30,0.12); border-radius:9px;"
            f"padding:1px 8px; font-size:11px; font-weight:700;"
        )
        title_row.addWidget(self.count_badge)
        title_row.addStretch()
        lay.addLayout(title_row)

        actions_row = QHBoxLayout()
        actions_row.setSpacing(10)
        scan_btn = ghost_btn("🔍  Scanner", self._scan)
        scan_btn.setFixedHeight(38)
        scan_btn.setStyleSheet(scan_btn.styleSheet() + "font-size:13px; padding:8px 18px; font-weight:700;")
        add_btn = ghost_btn("＋  Ajouter", self._add_account)
        add_btn.setFixedHeight(38)
        add_btn.setStyleSheet(add_btn.styleSheet() + "font-size:13px; padding:8px 18px; font-weight:700;")
        close_team_btn = QPushButton("✕  Fermer team")
        close_team_btn.setFixedHeight(38)
        close_team_btn.setStyleSheet(
            f"background:transparent;color:{RED};border:1px solid rgba(224,85,85,0.3);"
            f"border-radius:6px;padding:8px 18px;font-size:13px;font-weight:700;"
        )
        close_team_btn.clicked.connect(self._close_team)

        actions_row.addWidget(scan_btn)
        actions_row.addWidget(add_btn)
        actions_row.addStretch()
        actions_row.addWidget(close_team_btn)
        lay.addLayout(actions_row)

        self.scan_msg = QLabel("—")
        self.scan_msg.setWordWrap(True)
        self.scan_msg.setStyleSheet(f"color:{MUT}; font-size:11px; background:transparent;")
        lay.addWidget(self.scan_msg)

        self.empty_lbl = QLabel("Aucun compte détecté — clique sur « Scanner » avec Dofus ouvert.")
        self.empty_lbl.setWordWrap(True)
        self.empty_lbl.setStyleSheet(f"color:{MUT}; font-size:11px; background:transparent;")
        lay.addWidget(self.empty_lbl)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        rows_container = QWidget()
        self.rows_lay = QVBoxLayout(rows_container)
        self.rows_lay.setContentsMargins(0, 0, 0, 0)
        self.rows_lay.setSpacing(6)
        self.rows_lay.addStretch()
        scroll.setWidget(rows_container)
        lay.addWidget(scroll, stretch=1)

        return panel

    def _build_side_panel(self):
        side = QWidget()
        slay = QVBoxLayout(side)
        slay.setContentsMargins(0, 0, 0, 0)
        slay.setSpacing(16)
        slay.addWidget(self._banner_card())
        slay.addWidget(self._qa_card())
        slay.addStretch()
        return side

    def _banner_card(self):
        c = card(QWidget())
        c.setFixedWidth(240)
        lay = QVBoxLayout(c)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        img = QLabel()
        img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pix = QPixmap(str(SKIN_DIR / "dofus-unity.jpg"))
        if not pix.isNull():
            pix = pix.scaledToWidth(240, Qt.TransformationMode.SmoothTransformation)
            img.setFixedHeight(pix.height())
        img.setPixmap(pix)
        img.setStyleSheet("background:transparent; border-radius:10px;")
        lay.addWidget(img)

        return c

    def _qa_card(self):
        c = card(QWidget())
        c.setFixedWidth(240)
        lay = QVBoxLayout(c)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(8)

        lay.addWidget(section_label("Actions rapides"))

        self.spam_btn = QPushButton("🖱  Spam clic")
        self.spam_btn.setCheckable(True)
        self.spam_btn.setFixedHeight(36)
        self.spam_btn.setStyleSheet(
            f"background:{BG3};color:{TEXT};border:1px solid rgba(255,255,255,0.07);"
            f"border-radius:6px;padding:8px 12px;font-size:12.5px;font-weight:600;"
        )
        self.spam_btn.toggled.connect(self._toggle_spam)
        lay.addWidget(self.spam_btn)

        sort_btn = ghost_btn("📊 Trier la barre Windows", self._sort_taskbar)
        sort_btn.setFixedHeight(36)
        sort_btn.setStyleSheet(sort_btn.styleSheet() + "font-size:12.5px; padding:8px 12px; font-weight:600;")
        lay.addWidget(sort_btn)

        return c

    # ── rafraîchissement ────────────────────────────────────────────────
    def _refresh(self):
        order = self.config.get("custom_order", [])
        classes = self.config.get("classes", {})
        leader = self.config.get("leader_name", "")
        hwnds = {a.get("name"): a.get("hwnd") for a in (self.logic.all_accounts or [])}

        while self.rows_lay.count():
            item = self.rows_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._rows = {}

        from main import AccountRow  # import tardif — évite le cycle pages<->main

        for i, name in enumerate(order):
            acc = {
                "name": name,
                "classe": classes.get(name, ""),
                "leader": name == leader,
                "hwnd": hwnds.get(name),
            }
            row = AccountRow(acc, self.config, pos_num=i + 1)
            row.sig_remove.connect(self._remove)
            row.sig_up.connect(lambda n: self._move(n, -1))
            row.sig_down.connect(lambda n: self._move(n, 1))
            row.sig_leader.connect(self._set_leader)
            row.sig_close.connect(self._close_account)
            self.rows_lay.addWidget(row)
            self._rows[name] = row
        self.rows_lay.addStretch()

        self.count_badge.setText(str(len(order)))
        self.empty_lbl.setVisible(len(order) == 0)

        live = len([a for a in (self.logic.all_accounts or []) if a.get("hwnd")])
        self.scan_msg.setText(f"{live} fenêtre(s) Dofus détectée(s)")

        self.accounts_changed.emit(self.logic.all_accounts or [])

    def _rescan_refresh(self):
        self.logic.refresh_all()
        self._refresh()

    # ── actions ─────────────────────────────────────────────────────────
    def _scan(self):
        from main import ScanThread  # import tardif — évite le cycle pages<->main
        self.scan_msg.setText("Scan en cours…")

        def on_done(accounts):
            lv = len(accounts)
            if lv > 0:
                self.scan_msg.setText(f"✅  {lv} fenêtre(s) Dofus détectée(s)")
            else:
                self.scan_msg.setText("⚠  Aucune fenêtre Dofus — Dofus est-il ouvert ?")
            self._refresh()

        self._scan_thread = ScanThread(self.logic)
        self._scan_thread.done.connect(on_done)
        self._scan_thread.start()

    def _add_account(self):
        from main import CLASSES  # import tardif — évite le cycle pages<->main

        dlg = QDialog(self)
        dlg.setWindowTitle("Ajouter un compte")
        dlg.setMinimumWidth(340)
        dlg.setStyleSheet(STYLE)
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(12)

        lay.addWidget(section_label("Nom du compte"))
        name_inp = QLineEdit()
        name_inp.setFixedHeight(34)
        lay.addWidget(name_inp)

        lay.addWidget(section_label("Classe"))
        class_combo = QComboBox()
        class_combo.setFixedHeight(34)
        class_combo.addItems([""] + CLASSES)
        lay.addWidget(class_combo)

        def _confirm():
            name = name_inp.text().strip()
            if not name:
                return
            order = self.config.get("custom_order", [])
            if name not in order:
                order.append(name)
                self.config.set("custom_order", order)
            classes = self.config.get("classes", {})
            classes[name] = class_combo.currentText()
            self.config.set("classes", classes)
            self.config.save()
            dlg.accept()
            self._refresh()

        btn = accent_btn("Ajouter", _confirm)
        btn.setFixedHeight(38)
        lay.addWidget(btn)

        dlg.exec()

    def _remove(self, name):
        order = self.config.get("custom_order", [])
        if name in order:
            order.remove(name)
            self.config.set("custom_order", order)
        self.config.save()
        self._rescan_refresh()

    def _move(self, name, delta):
        self.logic.move_account(name, delta)
        self._refresh()

    def _set_leader(self, name):
        self.logic.set_leader(name)
        self._rescan_refresh()

    def _sort_taskbar(self):
        self.logic.sort_taskbar()

    def _close_account(self, name):
        acc = next((a for a in (self.logic.all_accounts or []) if a.get("name") == name), None)
        if acc and acc.get("hwnd"):
            self.logic.close_window(acc["hwnd"])
            # Report différé : on est encore dans le handler de clic du bouton
            # "⏻" de la ligne en train d'être fermée — reconstruire/détruire
            # cette ligne maintenant (via _rescan_refresh -> _refresh) plantait
            # l'appli. Même cause que le bug de drag&drop déjà corrigé.
            QTimer.singleShot(0, self._rescan_refresh)

    def _close_team(self):
        r = QMessageBox.question(
            self, "Fermer Team", "Fermer toutes les fenêtres Dofus actives ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if r == QMessageBox.StandardButton.Yes:
            self.logic.close_all()
            QTimer.singleShot(0, self._rescan_refresh)

    def _toggle_spam(self, on):
        if not PYAUTOGUI_OK:
            self.spam_btn.setChecked(False)
            return
        self._spam = on
        if on:
            iv = self.config.get("spam_click_interval", 0.1)

            def _s():
                while self._spam:
                    pyautogui.click()
                    time.sleep(iv)

            threading.Thread(target=_s, daemon=True).start()
        self.spam_btn.setStyleSheet(
            f"background:{'rgba(255,138,30,0.15)' if on else BG3};"
            f"color:{ACC if on else TEXT};"
            f"border:{'1px solid rgba(255,138,30,0.3)' if on else '1px solid rgba(255,255,255,0.07)'};"
            f"border-radius:6px;padding:6px;font-weight:{'700' if on else '400'};"
        )
