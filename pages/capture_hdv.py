"""Page « Capture HDV » — cadre de viseur à poser sur les prix de l'HDV pendant une session d'achat.

Le cadre (hdv_capture.py) lit la zone cadrée et envoie chaque capture à la page « Contribution au marché » du site
(hdv_bridge.py). Le site lit les prix et les met dans une liste : la validation (« Mettre à jour les prix ») se fait à la
fin de la session, sur le site. Ici : état de la connexion, cadre, réglages.
"""
import webbrowser

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox
from PyQt6.QtCore import Qt

from theme import TEXT, MUT, GREEN, GOLD, ACC, section_label, card, accent_btn, ghost_btn, mono

SITE_URL = "https://dofusteam.fr/hdv-scan"


def _make_header(title, subtitle):
    header = QWidget()
    header.setObjectName("PageHeader")
    lay = QVBoxLayout(header)
    lay.setContentsMargins(24, 18, 24, 14)
    lay.setSpacing(2)
    t = QLabel(title)
    t.setObjectName("PageTitle")
    lay.addWidget(t)
    s = QLabel(subtitle)
    s.setObjectName("PageSubtitle")
    s.setWordWrap(True)
    lay.addWidget(s)
    return header


def _muted(text):
    lbl = QLabel(text)
    lbl.setWordWrap(True)
    lbl.setStyleSheet(f"color:{MUT}; font-size:12px; background:transparent;")
    return lbl


class CaptureHdvPage(QWidget):
    def __init__(self, config, logic, capture, parent=None):
        super().__init__(parent)
        self.config = config
        self.capture = capture
        self._build()
        self.capture.status_changed.connect(self.refresh)
        self.refresh()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(_make_header(
            "Capture HDV",
            "Pose le cadre sur les prix de l'hôtel de vente : chaque fiche lue est envoyée au site, tu valides la liste à la fin de ta session.",
        ))

        body = QWidget()
        bl = QHBoxLayout(body)
        bl.setContentsMargins(24, 18, 24, 18)
        bl.setSpacing(16)

        # ── Colonne gauche : état + actions ───────────────────────────────────
        left = card(QWidget())
        ll = QVBoxLayout(left)
        ll.setContentsMargins(18, 16, 18, 16)
        ll.setSpacing(10)
        ll.addWidget(section_label("État"))
        self.site_lbl = QLabel()
        self.site_lbl.setStyleSheet("background:transparent; font-size:13px; font-weight:600;")
        ll.addWidget(self.site_lbl)
        self.site_hint = _muted("")
        ll.addWidget(self.site_hint)
        self.frame_lbl = QLabel()
        self.frame_lbl.setStyleSheet(f"color:{TEXT}; background:transparent; font-size:13px; font-weight:600;")
        ll.addWidget(self.frame_lbl)
        self.count_lbl = QLabel()
        self.count_lbl.setFont(mono(11))
        self.count_lbl.setStyleSheet(f"color:{MUT}; background:transparent;")
        ll.addWidget(self.count_lbl)
        self.err_lbl = _muted("")
        self.err_lbl.setStyleSheet("color:#fb923c; font-size:12px; background:transparent;")
        ll.addWidget(self.err_lbl)

        ll.addSpacing(6)
        row = QHBoxLayout()
        row.setSpacing(8)
        self.toggle_btn = ghost_btn("Afficher le cadre", self._toggle)
        row.addWidget(self.toggle_btn)
        row.addWidget(ghost_btn("Recentrer", self.capture.reset_frame))
        row.addStretch()
        ll.addLayout(row)
        row2 = QHBoxLayout()
        row2.setSpacing(8)
        self.run_btn = accent_btn("Démarrer la capture", self.capture.toggle_capture)
        row2.addWidget(self.run_btn)
        row2.addWidget(ghost_btn("Capturer maintenant", self.capture.capture_now))
        row2.addWidget(ghost_btn("Nouvelle session", self.capture.new_session))
        row2.addStretch()
        ll.addLayout(row2)
        ll.addWidget(ghost_btn("Ouvrir la page du site", lambda: webbrowser.open(SITE_URL)))

        ll.addSpacing(8)
        ll.addWidget(section_label("Réglages"))
        self.auto_chk = QCheckBox("Détection automatique")
        self.auto_chk.setChecked(self.capture.auto)
        self.auto_chk.toggled.connect(self.capture.set_auto)
        ll.addWidget(self.auto_chk)
        ll.addWidget(_muted("Lit la zone dès qu'elle change puis reste stable. Sans elle, utilise le raccourci ou le bouton ci-dessus."))
        ll.addWidget(_muted("Un objet déjà pris pendant la session n'est pas repris. « Nouvelle session » les oublie."))
        self.hk_lbl = _muted("")
        ll.addWidget(self.hk_lbl)
        ll.addStretch()
        bl.addWidget(left, 3)

        # ── Colonne droite : mode d'emploi ────────────────────────────────────
        right = card(QWidget())
        right.setFixedWidth(300)
        rl = QVBoxLayout(right)
        rl.setContentsMargins(18, 16, 18, 16)
        rl.setSpacing(10)
        rl.addWidget(section_label("Comment faire"))
        for n, text in (
            ("1", "Ouvre la page Contribution au marché du site dans ton navigateur et laisse-la ouverte."),
            ("2", "Affiche le cadre, glisse-le par son contour sur le tableau des prix de l'HDV, ajuste sa taille par un coin."),
            ("3", "Clique sur « Démarrer » (sous le cadre ou ici), puis ouvre tes fiches en jeu : à chaque lecture, une petite carte montre l'objet et ses prix."),
            ("4", "À la fin de ta session, valide la liste sur le site avec « Mettre à jour les prix »."),
        ):
            r = QHBoxLayout()
            r.setSpacing(10)
            num = QLabel(n)
            num.setFont(mono(12, True))
            num.setFixedWidth(16)
            num.setAlignment(Qt.AlignmentFlag.AlignTop)
            num.setStyleSheet(f"color:{ACC}; background:transparent;")
            r.addWidget(num)
            r.addWidget(_muted(text), 1)
            rl.addLayout(r)
        rl.addStretch()
        bl.addWidget(right, 0)

        lay.addWidget(body, 1)

    # ── Actions ───────────────────────────────────────────────────────────────
    def _toggle(self):
        self.capture.toggle_frame()

    def refresh(self):
        c = self.capture
        if c.connected:
            self.site_lbl.setText("●  Site connecté")
            self.site_lbl.setStyleSheet(f"color:{GREEN}; background:transparent; font-size:13px; font-weight:600;")
            self.site_hint.setText("Les captures arrivent dans la liste de la page Contribution au marché.")
        else:
            self.site_lbl.setText("●  Site non connecté")
            self.site_lbl.setStyleSheet(f"color:{GOLD}; background:transparent; font-size:13px; font-weight:600;")
            self.site_hint.setText("Ouvre la page Contribution au marché du site dans ton navigateur (Chrome conseillé).")
        self.frame_lbl.setText("Cadre : affiché" if c.frame_visible else "Cadre : masqué")
        self.toggle_btn.setText("Masquer le cadre" if c.frame_visible else "Afficher le cadre")
        self.run_btn.setText("Arrêter la capture" if c.running else "Démarrer la capture")
        self.count_lbl.setText(f"Session : {c.sent} envoyée(s) · {len(c.seen)} objet(s) distinct(s)")
        self.err_lbl.setText(c.last_error)
        self.err_lbl.setVisible(bool(c.last_error))
        hk = self.config.get("hdv_hotkey", "f8")
        tk = self.config.get("hdv_toggle_hotkey", "f9")
        parts = []
        if tk: parts.append(f"démarrer / arrêter : {tk.upper()}")
        if hk: parts.append(f"capture manuelle : {hk.upper()}")
        self.hk_lbl.setText("Raccourcis — " + " · ".join(parts) if parts else "Aucun raccourci défini")
