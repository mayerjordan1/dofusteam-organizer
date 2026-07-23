"""DofusTeam — invite_dialog.py"""
import threading, time, random
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

try:
    import pyautogui, pyperclip
    PYAUTOGUI_OK=True
except ImportError:
    PYAUTOGUI_OK=False

from paths import SKIN_DIR
from theme import BG, BG2, BG3, ACC, RED, TEXT, MUT as MUTED, GOLD, STYLE, make_avatar

class InviteDialog(QDialog):
    _status_sig = pyqtSignal(str)

    def __init__(self, config, logic, parent=None):
        super().__init__(parent)
        self.config = config
        self.logic  = logic
        self.setWindowTitle("👥 Inviter le groupe")
        self.setFixedSize(420, 500)
        self.setStyleSheet(STYLE)
        self._status_sig.connect(lambda m: self.status_lbl.setText(m))
        self._build()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(0,0,0,0)

        # Header
        hdr = QWidget(); hdr.setStyleSheet(f"background:{BG2};border-bottom:1px solid rgba(255,255,255,0.06);"); hdr.setFixedHeight(50)
        hl = QHBoxLayout(hdr); hl.setContentsMargins(16,0,16,0)
        tl = QLabel("👥  Inviter le groupe"); tl.setStyleSheet(f"font-size:15px;font-weight:700;font-family:'Space Mono',monospace;color:{TEXT};"); hl.addWidget(tl)
        lay.addWidget(hdr)

        content = QWidget(); cl = QVBoxLayout(content); cl.setContentsMargins(16,14,16,14); cl.setSpacing(12)

        # Chat position
        cp_frame = QFrame(); cp_frame.setStyleSheet(f"QFrame{{background:{BG2};border:1px solid rgba(255,255,255,0.07);border-radius:8px;}}")
        cpl = QHBoxLayout(cp_frame); cpl.setContentsMargins(12,8,12,8); cpl.setSpacing(8)
        cpl.addWidget(QLabel("Position chat :"))
        cp = self.config.get("macro_positions", {}).get("chat_position") or [794, 2025]
        self.cx = QSpinBox(); self.cx.setRange(0,9999); self.cx.setValue(cp[0] if cp else 794)
        self.cy = QSpinBox(); self.cy.setRange(0,9999); self.cy.setValue(cp[1] if cp else 2025)
        cpl.addWidget(QLabel("X:")); cpl.addWidget(self.cx)
        cpl.addWidget(QLabel("Y:")); cpl.addWidget(self.cy)
        cpl.addStretch()
        # Calibration status
        cp_status = QLabel("✅" if cp else "❌ Non calibré")
        cp_status.setStyleSheet(f"color:{'#27ae60' if cp else RED};font-size:11px;font-weight:600;")
        cpl.addWidget(cp_status)
        cl.addWidget(cp_frame)

        # Account list — auto from detected accounts
        list_title = QLabel("Personnages à inviter :")
        list_title.setStyleSheet(f"font-weight:700;color:{TEXT};"); cl.addWidget(list_title)

        hint = QLabel("Tous les personnages détectés (sauf le chef) seront invités.")
        hint.setStyleSheet(f"color:{MUTED};font-size:11px;"); cl.addWidget(hint)

        # Scroll list showing detected accounts with checkboxes
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        self.list_w = QWidget(); self.list_l = QVBoxLayout(self.list_w)
        self.list_l.setSpacing(4); self.list_l.setContentsMargins(0,0,0,0)
        scroll.setWidget(self.list_w); cl.addWidget(scroll)

        self.checkboxes = {}  # name -> QCheckBox
        self._populate_list()

        # Status
        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet(f"color:{ACC};font-size:11px;font-weight:600;"); self.status_lbl.setWordWrap(True)
        cl.addWidget(self.status_lbl)

        # Buttons
        btns = QHBoxLayout()
        refresh_btn = QPushButton("↻ Actualiser")
        refresh_btn.setStyleSheet(f"background:{BG3};border-radius:6px;padding:6px 14px;")
        refresh_btn.clicked.connect(self._populate_list); btns.addWidget(refresh_btn)
        btns.addStretch()
        go = QPushButton("🚀  Lancer les invitations")
        go.setStyleSheet(f"background:{ACC};color:#0f1115;border:none;border-radius:6px;padding:8px 20px;font-weight:700;font-size:13px;")
        go.clicked.connect(self._invite_all); btns.addWidget(go)
        cl.addLayout(btns)

        lay.addWidget(content)

    def _populate_list(self):
        # Clear
        while self.list_l.count():
            item = self.list_l.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        self.checkboxes = {}

        leader = self.config.get("leader_name", "")
        accounts = self.logic.all_accounts if self.logic else []

        if not accounts:
            self.list_l.addWidget(QLabel("Aucun compte détecté — scannez d'abord."))
            return

        for acc in accounts:
            name = acc["name"]
            is_leader = name == leader

            row = QWidget(); rl = QHBoxLayout(row); rl.setContentsMargins(4, 2, 4, 2); rl.setSpacing(8)

            # Avatar
            av = QLabel(); av.setFixedSize(28, 28)
            pix = make_avatar(acc.get("classe", ""))
            if pix: av.setPixmap(pix)
            rl.addWidget(av)

            # Checkbox + name
            chk = QCheckBox(name)
            chk.setChecked(not is_leader)  # Leader is pre-unchecked
            chk.setEnabled(not is_leader)
            if is_leader:
                chk.setStyleSheet(f"color:{MUTED};font-size:12px;")
                chk.setText(f"{name}  (chef — envoyeur)")
            else:
                chk.setStyleSheet(f"color:{TEXT};font-size:12px;font-weight:600;")
            rl.addWidget(chk)

            # Online indicator
            live = QLabel("●" if acc.get("hwnd") else "○")
            live.setStyleSheet(f"color:{'#27ae60' if acc.get('hwnd') else MUTED};font-size:12px;")
            rl.addWidget(live)
            rl.addStretch()

            self.checkboxes[name] = chk
            self.list_l.addWidget(row)

        self.list_l.addStretch()

    def _invite_all(self):
        if not PYAUTOGUI_OK:
            QMessageBox.warning(self, "Erreur", "pyautogui non installé."); return

        # Save chat position
        pos = self.config.get("macro_positions", {})
        pos["chat_position"] = [self.cx.value(), self.cy.value()]
        self.config.set("macro_positions", pos); self.config.save()

        # Get selected accounts (those checked and not leader)
        leader = self.config.get("leader_name", "")
        to_invite = [name for name, chk in self.checkboxes.items()
                     if chk.isChecked() and name != leader]

        if not to_invite:
            self._status_sig.emit("⚠ Aucun personnage sélectionné.")
            return

        # Switch to leader first
        if self.logic: self.logic.switch_to_leader()
        time.sleep(random.uniform(0.06, 0.14))

        cp = [self.cx.value(), self.cy.value()]
        total = len(to_invite)

        def _do():
            for i, name in enumerate(to_invite):
                self._status_sig.emit(f"Invitation {i+1}/{total} — {name}...")
                pyautogui.click(cp[0], cp[1]); time.sleep(0.2)
                pyperclip.copy(f"/invite {name}")
                pyautogui.hotkey("ctrl", "v"); pyautogui.press("enter")
                time.sleep(0.5)
            self._status_sig.emit(f"✅ {total} invitation(s) envoyée(s) !")

        threading.Thread(target=_do, daemon=True).start()
