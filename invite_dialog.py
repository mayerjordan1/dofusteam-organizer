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

from ui_kit import DtDialog, warn as _ui_warn


class InviteDialog(DtDialog):
    _status_sig = pyqtSignal(str)
    _done_sig = pyqtSignal()

    def __init__(self, config, logic, parent=None):
        super().__init__(parent, "Inviter le groupe", "Une invitation groupée, envoyée depuis le chat du chef.",
                         icon="icon_group.png", width=440, height=590)
        self.config = config
        self.logic  = logic
        self._status_sig.connect(lambda m: self.status_lbl.setText(m))
        self._done_sig.connect(lambda: QTimer.singleShot(900, self.close))
        self._build()

    def _build(self):
        cl = self.body

        # Chat calibration — juste un bouton qui bascule en confirmation verte
        # une fois calibré ; les coordonnées X/Y brutes n'intéressent personne.
        cp_frame = QFrame(); cp_frame.setObjectName("ChatFrame"); cp_frame.setStyleSheet(f"QFrame#ChatFrame{{background:{BG2};border:1px solid rgba(255,255,255,0.09);border-radius:10px;}} QFrame#ChatFrame QLabel{{background:transparent;border:none;}}")
        cpl = QHBoxLayout(cp_frame); cpl.setContentsMargins(12,8,12,8); cpl.setSpacing(8)
        cpl.addWidget(QLabel("Barre de chat du chef"))
        cpl.addStretch()
        self.calib_btn = QPushButton()
        self.calib_btn.clicked.connect(self._calibrate_chat)
        cpl.addWidget(self.calib_btn)
        self._update_calib_btn()
        cl.addWidget(cp_frame)

        # Account list — auto from detected accounts
        cl.addWidget(self.section("Personnages à inviter"))

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

        # Pied de page : invitation groupée (syntaxe confirmée en jeu : "/invite n1; /invite n2; ...").
        # L'ancien flow classique (_invite_all, 1 message/perso) reste dans le code, dormant, sans bouton.
        self.add_button("↻ Actualiser", "ghost", self._populate_list, min_width=110)
        self.add_button("Invitation groupée", "primary", self._invite_grouped, min_width=170)

    def _populate_list(self):
        # Clear
        while self.list_l.count():
            item = self.list_l.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        self.checkboxes = {}

        leader = self.config.get("leader_name", "")
        accounts = self.logic.all_accounts if self.logic else []
        accounts = sorted(accounts, key=lambda a: a["name"] != leader)

        if not accounts:
            _e = QLabel("Aucun compte détecté.\nLance d'abord un scan des fenêtres."); _e.setAlignment(Qt.AlignmentFlag.AlignCenter); _e.setStyleSheet(f"color:{MUTED};font-size:12px;padding:30px;"); self.list_l.addWidget(_e)
            return

        for acc in accounts:
            name = acc["name"]
            is_leader = name == leader

            row = QWidget(); rl = QHBoxLayout(row); rl.setContentsMargins(4, 2, 4, 2); rl.setSpacing(8)

            # Avatar
            av = QLabel(); av.setFixedSize(28, 28)
            pix = make_avatar(acc.get("classe", ""), 36, self.config.get("sexes", {}).get(name, "h"))   # sexe défini dans l'ordre d'initiative
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

    def _update_calib_btn(self):
        cp = self.config.get("macro_positions", {}).get("chat_position")
        if cp:
            self.calib_btn.setText("Chat calibré")
            self.calib_btn.setStyleSheet(
                f"background:transparent;color:#27ae60;border:none;font-size:12px;font-weight:700;padding:4px 8px;"
            )
        else:
            self.calib_btn.setText("Calibrer le chat")
            self.calib_btn.setStyleSheet(
                f"background:{BG3};color:{TEXT};border-radius:6px;padding:6px 12px;font-size:12px;font-weight:600;"
            )

    def _calibrate_chat(self):
        if not self.logic:
            self._status_sig.emit("Aucune connexion au jeu.")
            return
        from calibrator import CalibrationManager
        self._calib_mgr = CalibrationManager(self.config, self.logic, self, mode="chat")
        self._calib_mgr.status.connect(lambda m: self._status_sig.emit(m))
        self._calib_mgr.finished.connect(self._update_calib_btn)
        self._calib_mgr.start()

    def _invite_all(self):
        if not PYAUTOGUI_OK:
            _ui_warn(self, "Module manquant", "pyautogui n'est pas installé : lance install.bat."); return

        cp = self.config.get("macro_positions", {}).get("chat_position")
        if not cp:
            self._status_sig.emit("Chat non calibré.")
            return

        # Get selected accounts (those checked and not leader)
        leader = self.config.get("leader_name", "")
        to_invite = [name for name, chk in self.checkboxes.items()
                     if chk.isChecked() and name != leader]

        if not to_invite:
            self._status_sig.emit("Aucun personnage sélectionné.")
            return

        # Switch to leader first
        if self.logic: self.logic.switch_to_leader()
        time.sleep(random.uniform(0.06, 0.14))

        total = len(to_invite)

        def _do():
            for i, name in enumerate(to_invite):
                self._status_sig.emit(f"Invitation {i+1}/{total} — {name}...")
                pyautogui.click(cp[0], cp[1]); time.sleep(0.08)
                pyperclip.copy(f"/invite {name}")
                pyautogui.hotkey("ctrl", "v"); time.sleep(0.05)
                pyautogui.press("enter")
                time.sleep(0.2)
            self._status_sig.emit(f"{total} invitation(s) envoyée(s) !")
            self._done_sig.emit()

        threading.Thread(target=_do, daemon=True).start()

    def _invite_grouped(self):
        """Commande 3.7 confirmée en jeu — pas "/invite n1 ; n2 ; ..." (ça ne
        marchait pas) mais une chaîne de commandes /invite complètes séparées
        par "; " : "/invite n1; /invite n2; /invite n3". Reste chef-only
        (comme avant), donc réutilise chat_position (absolue, calibration
        existante) sans besoin de la calibration par-personnage (chat_multi),
        qui ne sert qu'à la macro /zaap collée dans chaque fenêtre."""
        if not PYAUTOGUI_OK:
            _ui_warn(self, "Module manquant", "pyautogui n'est pas installé : lance install.bat."); return

        cp = self.config.get("macro_positions", {}).get("chat_position")
        if not cp:
            self._status_sig.emit("Chat non calibré.")
            return

        leader = self.config.get("leader_name", "")
        to_invite = [name for name, chk in self.checkboxes.items()
                     if chk.isChecked() and name != leader]

        if not to_invite:
            self._status_sig.emit("Aucun personnage sélectionné.")
            return

        if self.logic: self.logic.switch_to_leader()
        time.sleep(random.uniform(0.06, 0.14))

        cmd = "; ".join(f"/invite {name}" for name in to_invite)

        def _do():
            self._status_sig.emit(f"Invitation groupée — {len(to_invite)} perso(s)...")
            pyautogui.click(cp[0], cp[1]); time.sleep(0.08)
            pyperclip.copy(cmd)
            pyautogui.hotkey("ctrl", "v"); time.sleep(0.08)
            pyautogui.press("enter")
            self._status_sig.emit(f"{len(to_invite)} invitation(s) envoyée(s) en un seul message !")
            self._done_sig.emit()

        threading.Thread(target=_do, daemon=True).start()
