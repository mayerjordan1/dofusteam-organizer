"""Page "Automatisations Zaap" — wrap plein-écran de l'onglet Exécution de
ZaapDialog (zaap_dialog.py), plus un lien de renvoi vers la page Calibration.

Décision du plan : zaap_dialog.py est le seul dialog dont le contenu interne
(QStackedWidget Calibration/Exécution) est directement repris/adapté comme
corps de page, plutôt qu'ouvert en modal. Ici seul l'onglet Exécution est
embarqué tel quel (mêmes signaux _status_sig/_phase2_sig/_done_sig, même
pilotage de ZaapExecutor via zaap_macro.py, aucune réécriture métier) ;
l'onglet Calibration est remplacé par une carte de renvoi vers la page
Calibration dédiée (pages/calibration.py) — décision "redondance calibration"
du plan, pour ne pas dupliquer CalibrationManager/zaap_dialog côte à côte.
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from PyQt6.QtCore import pyqtSignal

from theme import MUT, GOLD, RED, section_label, card, accent_btn, ghost_btn

try:
    import pyautogui, win32gui, win32api, win32process, ctypes
    pyautogui.FAILSAFE = False
    MACRO_OK = True
except ImportError:
    MACRO_OK = False


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


class AutomatisationsZaapPage(QWidget):
    """Page pleine largeur — pilote ZaapExecutor (phases 1/2/3) comme
    l'onglet Exécution de ZaapDialog, sans les tabs internes ni la taille
    fixe (pensés pour un QDialog, pas pour vivre dans le QStackedWidget)."""

    _status_sig = pyqtSignal(str)
    _phase2_sig = pyqtSignal()
    _done_sig = pyqtSignal()

    # Émis quand l'utilisateur clique "Aller à la Calibration" — MainWindow
    # peut s'y connecter pour naviguer vers la page Calibration une fois la
    # restructuration de la sidebar en place ; no-op tant que rien n'écoute.
    open_calibration = pyqtSignal()

    def __init__(self, config, logic, parent=None):
        super().__init__(parent)
        self.config = config
        self.logic = logic
        self.executor = None
        self._status_sig.connect(self._on_status)
        self._phase2_sig.connect(self._on_phase2)
        self._done_sig.connect(self._on_done)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        lay.addWidget(_make_header(
            "Automatisations Zaap",
            "Ouvre les havre-sacs et zaap tous les personnages vers une destination commune.",
        ))

        body = QWidget()
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(24, 18, 24, 18)
        body_lay.setSpacing(16)

        body_lay.addWidget(self._calib_link_card())
        body_lay.addWidget(self._exec_card())
        body_lay.addStretch()

        lay.addWidget(body)
        lay.addStretch()

    def _calib_link_card(self):
        c = card(QWidget())
        cl = QHBoxLayout(c)
        cl.setContentsMargins(16, 14, 16, 14)
        cl.setSpacing(12)

        txt = QVBoxLayout()
        txt.setSpacing(2)
        txt.addWidget(section_label("Calibration requise"))
        desc = QLabel("Chaque personnage doit être calibré (position du bouton zaap) avant de lancer l'automatisation.")
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color:{MUT}; font-size:11px; background:transparent;")
        txt.addWidget(desc)
        cl.addLayout(txt, stretch=1)

        cl.addWidget(ghost_btn("📍 Aller à la Calibration", self.open_calibration.emit))
        return c

    def _exec_card(self):
        c = card(QWidget())
        lay = QVBoxLayout(c)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(12)

        lay.addWidget(section_label("Exécution"))
        inst = QLabel(
            "1️⃣  <b>Phase 1</b> — L'app ouvre tous les havre-sacs et zaaps\n"
            "2️⃣  Sur le 1er perso : tape destination → Ctrl+A → Ctrl+C\n"
            "3️⃣  <b>Exécuter</b> — L'app colle et confirme sur tous les persos"
        )
        inst.setStyleSheet(f"color:{MUT};font-size:11px;")
        inst.setWordWrap(True)
        lay.addWidget(inst)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background:rgba(255,255,255,0.07);")
        lay.addWidget(sep)

        self.status_box = QLabel("En attente...")
        self.status_box.setStyleSheet(
            "background:#151922;border:1px solid rgba(255,255,255,0.07);border-radius:6px;padding:10px;font-size:12px;"
        )
        self.status_box.setWordWrap(True)
        self.status_box.setMinimumHeight(80)
        lay.addWidget(self.status_box)

        warn = QLabel("⚠️  Ne touchez pas la souris pendant l'exécution.")
        warn.setStyleSheet(f"color:{GOLD};font-size:10px;")
        lay.addWidget(warn)

        self.p1_btn = QPushButton("▶  Lancer Phase 1 — Ouvrir les Zaaps")
        self.p1_btn.setStyleSheet(
            "background:#ff8a1e;color:#0f1115;border:none;border-radius:6px;padding:10px;font-weight:700;font-size:13px;"
        )
        self.p1_btn.clicked.connect(self._launch_p1)
        lay.addWidget(self.p1_btn)

        self.exec_btn = QPushButton("⚡  Exécuter — Coller la destination")
        self.exec_btn.setStyleSheet(
            "background:#c8a000;color:white;border:none;border-radius:6px;padding:10px;font-weight:700;font-size:13px;"
        )
        self.exec_btn.setEnabled(False)
        self.exec_btn.clicked.connect(self._launch_p3)
        lay.addWidget(self.exec_btn)

        self.stop_btn = QPushButton("■  Arrêter")
        self.stop_btn.setStyleSheet(f"background:{RED};color:white;border:none;border-radius:6px;padding:6px;")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop)
        lay.addWidget(self.stop_btn)

        return c

    # ── pilotage ZaapExecutor (identique à ZaapDialog._launch_p1/_p3/_stop) ──
    def _launch_p1(self):
        if not self.logic or not MACRO_OK:
            self._on_status("Erreur: dépendances manquantes.")
            return
        self.p1_btn.setEnabled(False)
        self.exec_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        from zaap_macro import ZaapExecutor  # import tardif — évite le cycle pages<->main
        self.executor = ZaapExecutor(
            self.config, self.logic,
            on_status=lambda m: self._status_sig.emit(m),
            on_phase2_ready=lambda: self._phase2_sig.emit(),
            on_done=lambda: self._done_sig.emit(),
        )
        self.executor.start()

    def _launch_p3(self):
        if self.executor:
            self.exec_btn.setEnabled(False)
            self.executor.trigger_phase3()

    def _stop(self):
        if self.executor:
            self.executor.stop()
        self.p1_btn.setEnabled(True)
        self.exec_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self._on_status("Arrêté.")

    def _on_status(self, msg):
        self.status_box.setText(msg)

    def _on_phase2(self):
        self.exec_btn.setEnabled(True)
        self.exec_btn.setStyleSheet(
            "background:#ff8a1e;color:#0f1115;border:none;border-radius:6px;padding:10px;font-weight:700;font-size:13px;"
        )

    def _on_done(self):
        self.p1_btn.setEnabled(True)
        self.exec_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
