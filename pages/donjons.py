"""Page "Donjons" — fiches boss avec indications clé à garder sous la main.

Chaque boss ouvre une popup en 2 parties :
- Guide : contenu riche en lecture seule (titres colorés, emphases, images
  intégrées au fil du texte et cliquables pour zoomer) — curé à l'avance
  (par moi/Claude, à partir des liens/screens fournis) et codé en dur dans
  pages/donjon_guides.py (DEFAULT_GUIDES), PAS dans settings.json : ce
  fichier est local/gitignored donc absent sur une install fraîche, un
  guide qui n'existerait que là serait invisible pour tout le monde sauf
  la machine où il a été écrit. Les images qu'il référence vivent dans
  skin/ (bundlée par PyInstaller), jamais dans NOTES_IMG_DIR (contenu
  utilisateur, local). Pensé pour être lu EN JEU, d'un coup d'œil, pendant
  un tour compté — donc les images importantes sont affichées en taille
  lisible directement, pas juste en vignette.
- Mes notes : zone de texte libre, éditable, pour des rappels personnels
  rapides — persistée dans config["boss_notes"][boss_key].
Une galerie d'images "en vrac" (ajout via coller/fichier) reste disponible
sous les notes pour ce que l'utilisateur veut garder sans l'intégrer au
Guide — liste dans config["boss_notes_images"][boss_key], fichiers réels
dans NOTES_IMG_DIR/<boss_key>/ (cf. paths.py, à côté de settings.json donc
jamais perdus en onefile — même dossier que les images intégrées au Guide,
qui elles ne sont simplement pas ajoutées à cette liste).

Icônes attendues dans skin/ (mêmes conventions que le reste de l'app,
chargées via theme.load_icon) : "donjon.png" (icône de catégorie, sidebar)
et une icône par boss (cf. BOSSES ci-dessous) — absentes, un 💀 de secours
s'affiche à la place sans faire planter la page.
"""
import os
import shutil
import time

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QDialog, QTextEdit,
    QTextBrowser, QApplication, QScrollArea, QFileDialog, QPushButton,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap

from theme import TEXT, MUT, BG2, BG3, BORDER, ACC, STYLE, load_icon, ghost_btn
from paths import NOTES_IMG_DIR, SKIN_DIR
from pages.donjon_guides import DEFAULT_GUIDES

BOSS_ICON_SIZE = 84
THUMB_SIZE = 84
GRID_COLS = 4

# Un boss = { key (clé de sauvegarde stable, ne jamais renommer une fois des
# notes enregistrées), name (affiché), icon (fichier dans skin/), url (guide
# externe optionnel, lien cliquable en bas de la popup de notes) }.
BOSSES = [
    {
        "key": "harrebourg", "name": "Comte Harrebourg", "icon": "boss_harrebourg.png",
        "url": "https://www.dofuspourlesnoobs.com/donjon-du-comte-harebourg.html",
    },
    {
        "key": "vortex", "name": "Vortex", "icon": "boss_vortex.png",
        "url": "https://www.dofuspourlesnoobs.com/oeil-de-vortex.html",
    },
    {
        "key": "rdv", "name": "Reine des Voleurs", "icon": "boss_rdv.png",
        "url": "https://www.dofuspourlesnoobs.com/trone-de-la-cour-sombre.html",
    },
    {
        "key": "koutoulou", "name": "Koutoulou", "icon": "boss_koutoulou.png",
        "url": "https://www.dofuspourlesnoobs.com/temple-de-koutoulou.html",
    },
    {
        "key": "solar", "name": "Solar", "icon": "boss_solar.png",
        "url": "https://www.dofuspourlesnoobs.com/tour-de-solar.html",
    },
    {
        "key": "chaloeil", "name": "Chaloeil", "icon": "boss_chaloeil.png",
        "url": "https://www.dofuspourlesnoobs.com/defi-du-chaloeil.html",
    },
    {
        "key": "sylargh", "name": "Sylargh", "icon": "boss_sylargh.png",
        "url": "https://www.dofuspourlesnoobs.com/transporteur-de-sylargh.html",
    },
    {
        "key": "klime", "name": "Klime", "icon": "boss_klime.png",
        "url": "https://www.dofuspourlesnoobs.com/salons-priveacutes-de-klime.html",
    },
    {
        "key": "missiz_frizz", "name": "Missiz Frizz", "icon": "boss_missiz_frizz.png",
        "url": "https://www.dofuspourlesnoobs.com/forgefroide-de-missiz-frizz.html",
    },
    {
        "key": "nileza", "name": "Nileza", "icon": "boss_nileza.png",
        "url": "https://www.dofuspourlesnoobs.com/laboratoire-de-nileza.html",
    },
    {
        "key": "merkator", "name": "Merkator", "icon": "boss_merkator.png",
        "url": "https://www.dofuspourlesnoobs.com/aquadocircme-de-merkator.html",
    },
    {
        "key": "roi_nidas", "name": "Roi Nidas", "icon": "boss_roi_nidas.png",
        "url": "https://www.dofuspourlesnoobs.com/palais-du-roi-nidas.html",
    },
    {
        "key": "protozorreur", "name": "Protozorreur", "icon": "boss_protozorreur.png",
        "url": "https://www.dofuspourlesnoobs.com/ventre-de-la-baleine.html",
    },
    {
        "key": "capitaine_meno", "name": "Capitaine Meno", "icon": "boss_capitaine_meno.png",
        "url": "https://www.dofuspourlesnoobs.com/vaisseau-du-capitaine-meno.html",
    },
    {
        "key": "dantinea", "name": "Dantinéa", "icon": "boss_dantinea.png",
        "url": "https://www.dofuspourlesnoobs.com/palais-de-dantineacutea.html",
    },
    {
        "key": "tal_kasha", "name": "Tal Kasha", "icon": "boss_tal_kasha.png",
        "url": "https://www.dofuspourlesnoobs.com/chambre-de-tal-kasha.html",
    },
    {
        "key": "anerice", "name": "Anerice la Shushess", "icon": "boss_anerice_la_shushess.png",
        "url": "https://www.dofuspourlesnoobs.com/manoir-des-katrepat.html",
    },
    {
        "key": "ilyzaelle", "name": "Ilyzaelle", "icon": "boss_ilyzaelle.png",
        "url": "https://www.dofuspourlesnoobs.com/belvedere-d-ilyzaelle.html",
    },
    {
        "key": "bethel", "name": "Bethel Akarna", "icon": "boss_bethel_akarna.png",
        "url": "https://www.dofuspourlesnoobs.com/tour-de-bethel.html",
    },
    {
        "key": "dazak", "name": "Dazak Martegel", "icon": "boss_dazak_martegel.png",
        "url": "https://www.dofuspourlesnoobs.com/brasserie-du-roi-dazak.html",
    },
    {
        "key": "kao", "name": "Prêtresse de Kao", "icon": "boss_pretresse_de_kao.png",
        "url": "https://www.dofuspourlesnoobs.com/temple-du-dieu-kao.html",
    },
    {
        "key": "torkelonia", "name": "Torkélonia", "icon": "boss_torkelonia.png",
        "url": "https://www.dofuspourlesnoobs.com/sanctuaire-de-torkelonia.html",
    },
    {
        "key": "corruption", "name": "Corruption", "icon": "boss_corruption.png",
        "url": "https://www.dofuspourlesnoobs.com/arbre-de-mort.html",
    },
    {
        "key": "servitude", "name": "Servitude", "icon": "boss_servitude.png",
        "url": "https://www.dofuspourlesnoobs.com/fers-de-la-tyrannie.html",
    },
    {
        "key": "misere", "name": "Misère", "icon": "boss_misere.png",
        "url": "https://www.dofuspourlesnoobs.com/sentence-de-la-balance.html",
    },
    {
        "key": "guerre", "name": "Guerre", "icon": "boss_guerre.png",
        "url": "https://www.dofuspourlesnoobs.com/trone-de-sang.html",
    },
    {
        "key": "imagami", "name": "Roi Imagami", "icon": "boss_roi_imagami.png",
        "url": "https://www.dofuspourlesnoobs.com/memoire-d-orukam.html",
    },
    {
        "key": "amirukam", "name": "Reine Amirukam", "icon": "boss_reine_amirukam.png",
        "url": "https://www.dofuspourlesnoobs.com/souvenir-d-imagiro.html",
    },
    {
        "key": "kabahal", "name": "Kabahal", "icon": "boss_kabahal.png",
        "url": "https://www.dofuspourlesnoobs.com/rituel-de-kabahal.html",
    },
    {
        "key": "eternel_conflit", "name": "L'Éternel Conflit", "icon": "boss_l_eternel_conflit.png",
        "url": "https://www.dofuspourlesnoobs.com/bataille-de-l-aurore-pourpre.html",
    },
    {
        "key": "belladone", "name": "Belladone", "icon": "boss_belladone.png",
        "url": "https://www.dofuspourlesnoobs.com/chambre-des-malefices.html",
    },
    {
        "key": "venerable", "name": "Vénérable Endormi", "icon": "boss_venerable_endormi.png",
        "url": "https://www.dofuspourlesnoobs.com/breuil-du-venerable.html",
    },
    {
        "key": "dechireuse", "name": "Déchireuse", "icon": "boss_dechireuse.png",
        "url": "https://www.dofuspourlesnoobs.com/autel-de-la-dechireuse.html",
    },
]


# Avis de recherche de niveau 200 (même popup que les boss ; clés préfixées « w_ »).
RECHERCHES = [
    {
        "key": "w_chevalier_glace", "name": "Chevalier de Glace", "icon": "recherche_chevalier_glace.png",
        "url": "https://www.dofuspourlesnoobs.com/on-recherche-le-chevalier-de-glace.html",
    },
    {
        "key": "w_culbutoeuf", "name": "Culbutoeuf", "icon": "recherche_culbutoeuf.png",
        "url": "https://www.dofuspourlesnoobs.com/on-recherche-culbutoeuf.html",
    },
    {
        "key": "w_mekamouth", "name": "Mekamouth", "icon": "recherche_mekamouth.png",
        "url": "https://www.dofuspourlesnoobs.com/on-recherche-mekamouth.html",
    },
    {
        "key": "w_takomako", "name": "Takomako", "icon": "recherche_takomako.png",
        "url": "https://www.dofuspourlesnoobs.com/on-recherche-takomako.html",
    },
    {
        "key": "w_homard_medali", "name": "Homard Medali", "icon": "recherche_homard_medali.png",
        "url": "https://www.dofuspourlesnoobs.com/on-recherche-le-homard-medali.html",
    },
    {
        "key": "w_atcham", "name": "Atcham", "icon": "recherche_atcham.png",
        "url": "https://www.dofuspourlesnoobs.com/on-recherche-atcham.html",
    },
    {
        "key": "w_buldalazred", "name": "Buldalazred", "icon": "recherche_buldalazred.png",
        "url": "https://www.dofuspourlesnoobs.com/on-recherche-buldalazred.html",
    },
    {
        "key": "w_ganos", "name": "Ganos", "icon": "recherche_ganos.png",
        "url": "https://www.dofuspourlesnoobs.com/on-recherche-ganos.html",
    },
    {
        "key": "w_glourdorak", "name": "Glourdorak", "icon": "recherche_glourdorak.png",
        "url": "https://www.dofuspourlesnoobs.com/on-recherche-glourdorak.html",
    },
    {
        "key": "w_kongoku", "name": "Grand Kongoku", "icon": "recherche_kongoku.png",
        "url": "https://www.dofuspourlesnoobs.com/on-recherche-le-grand-kongoku.html",
    },
    {
        "key": "w_hyperscampe", "name": "Hyperscampe", "icon": "recherche_hyperscampe.png",
        "url": "https://www.dofuspourlesnoobs.com/on-recherche-l-hyperscampe.html",
    },
    {
        "key": "w_khepricorne", "name": "Khepricorne", "icon": "recherche_khepricorne.png",
        "url": "https://www.dofuspourlesnoobs.com/on-recherche-le-khepricorne.html",
    },
    {
        "key": "w_braideur", "name": "Fantôme Braïdeur", "icon": "recherche_braideur.png",
        "url": "https://www.dofuspourlesnoobs.com/on-recherche-le-fantome-braideur.html",
    },
    {
        "key": "w_psikopompe", "name": "Psikopompe", "icon": "recherche_psikopompe.png",
        "url": "https://www.dofuspourlesnoobs.com/on-recherche-le-psikopompe.html",
    },
    {
        "key": "w_sicogne", "name": "Sicogne", "icon": "recherche_sicogne.png",
        "url": "https://www.dofuspourlesnoobs.com/on-recherche-sicogne.html",
    },
    {
        "key": "w_voldelor", "name": "Voldelor", "icon": "recherche_voldelor.png",
        "url": "https://www.dofuspourlesnoobs.com/on-recherche-voldelor.html",
    },
]


def _boss_img_dir(boss_key):
    d = NOTES_IMG_DIR / boss_key
    d.mkdir(parents=True, exist_ok=True)
    return d


def _make_header(title, subtitle):
    header = QWidget()
    header.setObjectName("PageHeader")
    lay = QVBoxLayout(header)
    lay.setContentsMargins(24, 18, 24, 14)
    lay.setSpacing(2)

    title_row = QHBoxLayout()
    title_row.setSpacing(8)
    icon = load_icon("donjon.png", 22)
    if icon:
        icon_lbl = QLabel()
        icon_lbl.setPixmap(icon.pixmap(22, 22))
        icon_lbl.setStyleSheet("background:transparent; border:none;")
        title_row.addWidget(icon_lbl)
    t = QLabel(title)
    t.setObjectName("PageTitle")
    title_row.addWidget(t)
    title_row.addStretch()
    lay.addLayout(title_row)

    if subtitle:
        s = QLabel(subtitle)
        s.setObjectName("PageSubtitle")
        s.setWordWrap(True)
        lay.addWidget(s)
    return header


class BossCard(QWidget):
    """Tuile cliquable icône+nom — même pattern clic-sans-drag que
    theme.ClickableAvatar, dupliqué ici car spécifique à une mise en page
    verticale (icône au-dessus du nom) qu'un QPushButton standard ne permet
    pas nativement (icône toujours à gauche du texte)."""
    clicked = pyqtSignal()

    def __init__(self, boss, parent=None):
        super().__init__(parent)
        self._press_pos = None
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(150, 170)
        self.setObjectName(f"BossCard_{boss['key']}")
        self.setStyleSheet(
            f"QWidget#{self.objectName()} {{ background:{BG2}; border:1px solid {BORDER}; border-radius:12px; }}"
            f"QWidget#{self.objectName()}:hover {{ border:1px solid {ACC}; }}"
        )

        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 16, 12, 12)
        lay.setSpacing(10)

        icon_lbl = QLabel()
        icon_lbl.setFixedSize(BOSS_ICON_SIZE, BOSS_ICON_SIZE)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet("background:transparent; border:none;")
        icon = load_icon(boss["icon"], BOSS_ICON_SIZE)
        if icon:
            icon_lbl.setPixmap(icon.pixmap(BOSS_ICON_SIZE, BOSS_ICON_SIZE))
        else:
            icon_lbl.setText("💀")
            icon_lbl.setStyleSheet(f"background:transparent; border:none; font-size:40px; color:{MUT};")
        lay.addWidget(icon_lbl, 0, Qt.AlignmentFlag.AlignHCenter)

        name_lbl = QLabel(boss["name"])
        name_lbl.setWordWrap(True)
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_lbl.setStyleSheet(f"color:{TEXT}; font-size:13px; font-weight:700; background:transparent; border:none;")
        lay.addWidget(name_lbl)

    def mousePressEvent(self, event):
        self._press_pos = event.position().toPoint()
        event.ignore()

    def mouseReleaseEvent(self, event):
        if self._press_pos is not None:
            moved = (event.position().toPoint() - self._press_pos).manhattanLength()
            if moved < QApplication.startDragDistance():
                self.clicked.emit()
        self._press_pos = None
        event.ignore()


class ImageViewerDialog(QDialog):
    """Aperçu plein format d'une image de note — clic sur une vignette."""

    def __init__(self, path, parent=None):
        super().__init__(parent)
        self.setWindowTitle(path.name)
        self.setStyleSheet(STYLE)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

        pix = QPixmap(str(path))
        screen = QApplication.primaryScreen()
        max_w = int(screen.availableGeometry().width() * 0.8) if screen else 1200
        max_h = int(screen.availableGeometry().height() * 0.8) if screen else 800
        if pix.width() > max_w or pix.height() > max_h:
            pix = pix.scaled(max_w, max_h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(8)
        img_lbl = QLabel()
        img_lbl.setPixmap(pix)
        lay.addWidget(img_lbl)
        close_row = QHBoxLayout()
        close_row.addStretch()
        close_row.addWidget(ghost_btn("Fermer", self.close))
        lay.addLayout(close_row)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)


class _ClickableLabel(QLabel):
    """QLabel cliquable minimal — pas de seuil anti-drag ici (contrairement à
    ClickableAvatar/BossCard) : une vignette d'image fixe n'est jamais une
    source de drag&drop dans cette page, un simple mousePressEvent suffit."""
    clicked = pyqtSignal()

    def mousePressEvent(self, event):
        self.clicked.emit()
        event.ignore()


class ImageThumb(QWidget):
    """Vignette d'une image de note — clic = aperçu plein format, ✕ = suppression."""
    view_requested = pyqtSignal()
    remove_requested = pyqtSignal()

    def __init__(self, path, parent=None):
        super().__init__(parent)
        self.setFixedWidth(THUMB_SIZE)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)

        pic = _ClickableLabel()
        pic.setFixedSize(THUMB_SIZE, THUMB_SIZE)
        pic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pic.setCursor(Qt.CursorShape.PointingHandCursor)
        pic.setStyleSheet(f"background:{BG3}; border:1px solid {BORDER}; border-radius:8px;")
        pix = QPixmap(str(path))
        if not pix.isNull():
            pix = pix.scaled(THUMB_SIZE - 6, THUMB_SIZE - 6, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            pic.setPixmap(pix)
        pic.clicked.connect(self.view_requested.emit)
        lay.addWidget(pic)

        rm = QPushButton("✕ Retirer")
        rm.setCursor(Qt.CursorShape.PointingHandCursor)
        rm.setStyleSheet(f"background:transparent; color:{MUT}; border:none; font-size:9.5px;")
        rm.clicked.connect(self.remove_requested.emit)
        lay.addWidget(rm, 0, Qt.AlignmentFlag.AlignHCenter)


class BossNotesDialog(QDialog):
    """Popup de notes pour un boss — texte libre + galerie d'images de
    référence (schémas de ciblage, captures d'état...), à garder sous les
    yeux pendant le combat.

    Reste au-dessus de tout (y compris la fenêtre du jeu) et ne se ferme
    jamais en cliquant ailleurs — ouverte en non-modal (show(), pas exec())
    pour ne pas non plus bloquer le reste de l'organizer."""

    def __init__(self, config, boss, parent=None):
        super().__init__(parent)
        self.config = config
        self.boss = boss
        self.setWindowTitle(boss["name"])
        self.resize(560, 800)
        self.setMinimumSize(420, 420)
        self.setStyleSheet(STYLE)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        # Détruite (pas juste cachée) à la fermeture — nécessaire pour que
        # DonjonsPage._dialogs (tracking anti-doublon) se nettoie via le
        # signal `destroyed` et qu'une réouverture recrée bien la fenêtre.
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        hdr = QWidget()
        hdr.setStyleSheet(f"background:{BG2};border-bottom:1px solid rgba(255,255,255,0.06);")
        hdr.setFixedHeight(56)
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(16, 0, 16, 0)
        hl.setSpacing(10)
        icon = load_icon(self.boss["icon"], 30)
        if icon:
            icon_lbl = QLabel()
            icon_lbl.setPixmap(icon.pixmap(30, 30))
            icon_lbl.setStyleSheet("background:transparent;border:none;")
            hl.addWidget(icon_lbl)
        tl = QLabel(self.boss["name"])
        tl.setStyleSheet(
            f"font-size:15px;font-weight:700;font-family:'Space Mono',monospace;"
            f"color:{TEXT};background:transparent;border:none;"
        )
        hl.addWidget(tl)
        hl.addStretch()
        lay.addWidget(hdr)

        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(16, 14, 16, 14)
        cl.setSpacing(10)

        guide_html = DEFAULT_GUIDES.get(self.boss["key"], "")

        # ── Bloc du bas : Mes notes + galerie (toujours présent) ────────
        bottom = QWidget()
        bl = QVBoxLayout(bottom)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.setSpacing(10)

        notes_title = QLabel("Mes notes")
        notes_title.setStyleSheet(f"color:{MUT}; font-size:10px; font-weight:700; letter-spacing:1px; background:transparent; border:none;")
        bl.addWidget(notes_title)

        self.notes = QTextEdit()
        self.notes.setPlaceholderText("Rappels personnels rapides, en plus du Guide ci-dessus...")
        self.notes.setStyleSheet(
            f"QTextEdit {{ background:{BG2}; color:{TEXT}; border:1px solid {BORDER}; "
            f"border-radius:8px; padding:10px; font-size:12px; }}"
        )
        notes = self.config.get("boss_notes", {})
        self.notes.setPlainText(notes.get(self.boss["key"], ""))
        bl.addWidget(self.notes, 1)

        # ── Galerie d'images en vrac ─────────────────────────────────────
        img_row = QHBoxLayout()
        img_title = QLabel("Autres images")
        img_title.setStyleSheet(f"color:{MUT}; font-size:10px; font-weight:700; letter-spacing:1px; background:transparent; border:none;")
        img_row.addWidget(img_title)
        img_row.addStretch()
        img_row.addWidget(ghost_btn("Coller", self._paste_image))
        img_row.addWidget(ghost_btn("Ajouter", self._add_image_file))
        bl.addLayout(img_row)

        self._strip_scroll = QScrollArea()
        self._strip_scroll.setWidgetResizable(True)
        self._strip_scroll.setFixedHeight(THUMB_SIZE + 34)
        self._strip_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._strip_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._strip_scroll.setStyleSheet("background:transparent; border:none;")
        self._strip_w = QWidget()
        self._strip_w.setStyleSheet("background:transparent;")
        self._strip_lay = QHBoxLayout(self._strip_w)
        self._strip_lay.setContentsMargins(0, 0, 0, 0)
        self._strip_lay.setSpacing(8)
        self._strip_lay.addStretch()
        self._strip_scroll.setWidget(self._strip_w)
        bl.addWidget(self._strip_scroll)

        self._empty_hint = QLabel("Aucune image — colle une capture (Ctrl+C dans le jeu) ou ajoute un fichier.")
        self._empty_hint.setStyleSheet(f"color:{MUT}; font-size:10.5px; background:transparent; border:none;")
        bl.addWidget(self._empty_hint)

        self._refresh_images()

        btns = QHBoxLayout()
        if self.boss.get("url"):
            link = QLabel(f'<a href="{self.boss["url"]}" style="color:{ACC};">🔗 Guide complet (dofuspourlesnoobs.com)</a>')
            link.setStyleSheet("background:transparent; border:none; font-size:11px;")
            link.setOpenExternalLinks(True)
            btns.addWidget(link)
        btns.addStretch()
        btns.addWidget(ghost_btn("Fermer", self.close))
        bl.addLayout(btns)

        # ── Guide (riche, lecture seule, curé à l'avance) ───────────────
        if guide_html:
            top = QWidget()
            tl_ = QVBoxLayout(top)
            tl_.setContentsMargins(0, 0, 0, 0)
            tl_.setSpacing(10)

            self.guide = QTextBrowser()
            self.guide.setOpenLinks(False)
            self.guide.anchorClicked.connect(self._on_guide_link)
            self.guide.setStyleSheet(
                f"QTextBrowser {{ background:{BG2}; color:{TEXT}; border:1px solid {BORDER}; "
                f"border-radius:8px; padding:12px; font-size:12.5px; }}"
            )
            # Le HTML curé référence ses images par simple nom de fichier (ex:
            # src="guide_etat.png") — jamais de chemin absolu (non portable
            # entre installs). setSearchPaths() les résout contre 2 dossiers :
            # les images propres à CE boss (schémas...) et skin/ (icônes de
            # stats/états partagées, réutilisables par tous les guides).
            self.guide.setSearchPaths([str(_boss_img_dir(self.boss["key"])), str(SKIN_DIR)])
            self.guide.setHtml(guide_html)
            tl_.addWidget(self.guide, 1)

            # ── Onglets Guide / Notes & images ──────────────────────────
            # Un simple empilement (ou même un splitter, cf. anciennes
            # versions) partageait toujours la hauteur entre les deux — le
            # Guide restait petit dès que Mes notes/galerie prenaient de la
            # place. En onglets, chacun a TOUTE la hauteur de la popup :
            # le Guide est bien plus grand par défaut, sans rien à ajuster.
            tab_row = QHBoxLayout()
            tab_row.setSpacing(6)
            self._tab_guide_btn = self._tab_btn("Guide", lambda: self._switch_tab("guide"))
            self._tab_notes_btn = self._tab_btn("Mes notes && images", lambda: self._switch_tab("notes"))
            tab_row.addWidget(self._tab_guide_btn)
            tab_row.addWidget(self._tab_notes_btn)
            tab_row.addStretch()
            cl.addLayout(tab_row)

            self._tab_panels = {"guide": top, "notes": bottom}
            cl.addWidget(top, 1)
            cl.addWidget(bottom, 1)
            self._switch_tab("guide")
        else:
            cl.addWidget(bottom, 1)

        lay.addWidget(content, 1)

    def _tab_btn(self, label, onclick):
        btn = QPushButton(label)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(onclick)
        return btn

    def _switch_tab(self, key):
        for k, panel in self._tab_panels.items():
            panel.setVisible(k == key)
        active_style = (
            f"QPushButton {{ background:{ACC}22; color:{TEXT}; border:1px solid {ACC}; "
            f"border-radius:7px; padding:6px 12px; font-size:11.5px; font-weight:700; }}"
        )
        inactive_style = (
            f"QPushButton {{ background:transparent; color:{MUT}; border:1px solid {BORDER}; "
            f"border-radius:7px; padding:6px 12px; font-size:11.5px; }}"
            f"QPushButton:hover {{ color:{TEXT}; border-color:{ACC}; }}"
        )
        self._tab_guide_btn.setStyleSheet(active_style if key == "guide" else inactive_style)
        self._tab_notes_btn.setStyleSheet(active_style if key == "notes" else inactive_style)

    # ── Galerie : chargement / ajout / suppression ─────────────────────────
    def _image_list(self):
        images = self.config.get("boss_notes_images", {})
        return images.get(self.boss["key"], [])

    def _set_image_list(self, filenames):
        images = self.config.get("boss_notes_images", {})
        images[self.boss["key"]] = filenames
        self.config.set("boss_notes_images", images)
        self.config.save()

    def _refresh_images(self):
        while self._strip_lay.count() > 1:
            item = self._strip_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        filenames = self._image_list()
        boss_dir = _boss_img_dir(self.boss["key"])
        for fname in filenames:
            path = boss_dir / fname
            if not path.exists():
                continue
            thumb = ImageThumb(path)
            thumb.view_requested.connect(lambda p=path: self._view_image(p))
            thumb.remove_requested.connect(lambda f=fname: self._remove_image(f))
            self._strip_lay.insertWidget(self._strip_lay.count() - 1, thumb)

        self._empty_hint.setVisible(len(filenames) == 0)

    def _view_image(self, path):
        dlg = ImageViewerDialog(path, self)
        dlg.exec()

    def _on_guide_link(self, url):
        # Les images intégrées au Guide sont enveloppées dans <a href="zoom:
        # <fichier>"> (cf. contenu HTML curé) pour rester "coup d'œil" par
        # défaut (déjà affichées en taille lisible) tout en permettant un
        # agrandissement plein format au clic, comme la galerie du bas.
        # setOpenLinks(False) empêche déjà toute navigation réelle — un lien
        # externe éventuel dans le Guide est donc silencieusement ignoré ici.
        raw = url.toString()
        if raw.startswith("zoom:"):
            fname = raw[len("zoom:"):]
            path = _boss_img_dir(self.boss["key"]) / fname
            if not path.exists():
                path = SKIN_DIR / fname  # images curées du Guide (bundlées)
            if path.exists():
                self._view_image(path)

    def _remove_image(self, filename):
        boss_dir = _boss_img_dir(self.boss["key"])
        try:
            (boss_dir / filename).unlink(missing_ok=True)
        except Exception:
            pass
        filenames = [f for f in self._image_list() if f != filename]
        self._set_image_list(filenames)
        self._refresh_images()

    def _store_pixmap(self, pix):
        if pix.isNull():
            return
        boss_dir = _boss_img_dir(self.boss["key"])
        fname = f"img_{int(time.time() * 1000)}.png"
        pix.save(str(boss_dir / fname), "PNG")
        filenames = self._image_list() + [fname]
        self._set_image_list(filenames)
        self._refresh_images()

    def _add_image_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Ajouter une image", "", "Images (*.png *.jpg *.jpeg *.webp *.bmp)"
        )
        if not path:
            return
        boss_dir = _boss_img_dir(self.boss["key"])
        fname = f"img_{int(time.time() * 1000)}{os.path.splitext(path)[1].lower()}"
        try:
            shutil.copy(path, boss_dir / fname)
        except Exception:
            return
        filenames = self._image_list() + [fname]
        self._set_image_list(filenames)
        self._refresh_images()

    def _paste_image(self):
        img = QApplication.clipboard().image()
        if img.isNull():
            self._empty_hint.setText("Presse-papiers vide ou sans image — copie une capture d'écran puis réessaie.")
            self._empty_hint.setVisible(True)
            return
        self._store_pixmap(QPixmap.fromImage(img))

    def closeEvent(self, event):
        # Seul point de sauvegarde du texte — passé aussi bien par le bouton
        # "Fermer" (self.close()) que par la croix de la fenêtre. Les images
        # sont, elles, sauvegardées immédiatement à l'ajout/suppression (pas
        # besoin d'attendre la fermeture).
        notes = self.config.get("boss_notes", {})
        notes[self.boss["key"]] = self.notes.toPlainText()
        self.config.set("boss_notes", notes)
        self.config.save()
        event.accept()


# ── Tableau « États de déplacement » (refait à partir du tableau de Coverer) ──
# colonnes = états ; ligne = (libellé, sous-titre/sort, icône, [True = déplacement possible]) 
MOVE_STATES = [
    ("Pesanteur", "etat_pesanteur.png"), ("Lourd", "etat_lourd.png"), ("Enraciné", "etat_enracine.png"),
    ("Indéplaçable", "etat_indeplacable.png"), ("Inébranlable", "etat_inebranlable.png"),
]
MOVE_ROWS = [
    ("Attirer", "sort Attirance", "dep_attirance.png", [True, True, False, False, False]),
    ("Pousser", "sort Libération", "dep_liberation.png", [True, True, False, False, False]),
    ("Téléporter", "sort Bond", "dep_bond.png", [False, True, True, True, True]),
    ("Échanger", "échange de position", "dep_echanger.png", [False, True, False, False, True]),
    ("Porter", "Pandawa", "pandawa_h.png", [True, False, True, False, True]),
    ("Portail", "Eliotrope", "dep_portail.png", [True, True, False, False, True]),
]
MOVE_NOTES = [
    "Des exceptions s'appliquent pour certains gardiens de donjon.",
    "Les sorts qui provoquent un <b>changement de position</b> suivent la rangée « <b>Échanger</b> », "
    "même lors d'un atterrissage sur une case libre (ce n'est donc pas une Téléportation !).",
    "Exemples : Projection du Sacrieur · Éviction du Pandawa · tout sort de déplacement Xélor.",
]


def moves_table_html():
    """Tableau lisible dans un QTextBrowser (icônes de skin/, thème DofusTeam)."""
    ok = f'<span style="color:#6dc96d; font-size:20px; font-weight:700;">&#10003;</span>'
    ko = f'<span style="color:#e05c5c; font-size:18px; font-weight:700;">&#10005;</span>'
    th = "".join(
        f'<td width="104" align="center" style="padding:8px 4px;"><img src="{ic}" width="34" height="34"><br>'
        f'<span style="font-size:11px; font-weight:700;">{name}</span></td>' for name, ic in MOVE_STATES)
    rows = ""
    for label, sub, icon, cells in MOVE_ROWS:
        tds = "".join(f'<td align="center" bgcolor="#161b22" style="padding:6px;">{ok if c else ko}</td>' for c in cells)
        rows += (f'<tr><td width="200" bgcolor="#161b22" style="padding:6px 10px;"><img src="{icon}" width="30" height="30" '
                 f'align="middle">&nbsp;&nbsp;<b>{label}</b><br><span style="font-size:10px; color:#7a7d8a;">{sub}</span></td>{tds}</tr>')
    notes = "".join(f'<li style="margin-bottom:6px;">{n}</li>' for n in MOVE_NOTES)
    return (f'<p style="font-size:12px; color:#7a7d8a; margin:0 0 10px 0;">'
            f'<b style="color:#6dc96d;">&#10003;</b> le déplacement fonctionne malgré l\'état &nbsp;·&nbsp; '
            f'<b style="color:#e05c5c;">&#10005;</b> bloqué par l\'état</p>'
            f'<table cellspacing="4" cellpadding="0" width="740"><tr><td width="200"></td>{th}</tr>{rows}</table>'
            f'<ul style="margin:14px 0 6px 0; padding-left:18px; color:#e8e9ed;">{notes}</ul>'
            f'<p style="font-size:10px; color:#7a7d8a;">Tableau d\'origine : Coverer (Coverer Dofus sur YouTube).</p>')


class DonjonsPage(QWidget):
    """Grille de boss — clic = ouvre les indications de combat associées."""

    def __init__(self, config, logic, parent=None):
        super().__init__(parent)
        self.config = config
        self.logic = logic
        self._dialogs = {}  # boss key -> BossNotesDialog déjà ouverte (évite les doublons)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        lay.addWidget(_make_header(
            "Donjons",
            "Clique sur un boss pour consulter/éditer les indications clé du combat.",
        ))

        # Onglets du haut : Donjons · Avis de recherche · Déplacements
        tabs_row = QHBoxLayout()
        tabs_row.setContentsMargins(24, 12, 24, 0)
        tabs_row.setSpacing(6)
        self._page_tab_btns = {}
        self._page_panels = {}
        content = QVBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)

        def _scroll(inner):
            sc = QScrollArea()
            sc.setWidgetResizable(True)
            sc.setFrameShape(QScrollArea.Shape.NoFrame)
            sc.setStyleSheet("QScrollArea { background:transparent; border:none; }")
            sc.setWidget(inner)
            return sc

        def _grid_panel(items):
            body = QWidget()
            body_lay = QVBoxLayout(body)
            body_lay.setContentsMargins(24, 18, 24, 18)
            body_lay.setSpacing(12)
            grid = QWidget()
            grid.setStyleSheet("background:transparent;")
            grid_lay = QGridLayout(grid)
            grid_lay.setContentsMargins(0, 0, 0, 0)
            grid_lay.setSpacing(14)
            grid_lay.setAlignment(Qt.AlignmentFlag.AlignLeft)
            for i, boss in enumerate(items):
                tile = BossCard(boss)
                tile.clicked.connect(lambda b=boss: self._open_boss(b))
                grid_lay.addWidget(tile, i // GRID_COLS, i % GRID_COLS)
            body_lay.addWidget(grid)
            body_lay.addStretch()
            return _scroll(body)

        def _moves_panel():
            body = QWidget()
            body_lay = QVBoxLayout(body)
            body_lay.setContentsMargins(24, 18, 24, 18)
            tb = QTextBrowser()
            tb.setOpenLinks(False)
            tb.setSearchPaths([str(SKIN_DIR)])
            tb.setFrameShape(QTextBrowser.Shape.NoFrame)
            tb.setStyleSheet(f"QTextBrowser {{ background:transparent; color:{TEXT}; border:none; font-size:12px; }}")
            tb.setHtml(moves_table_html())
            tb.setMinimumWidth(780)
            tb.setMaximumWidth(860)
            body_lay.addWidget(tb, 1)
            body_lay.addStretch(0)
            return body

        panels = [
            ("donjons", f"Donjons ({len(BOSSES)})", _grid_panel(BOSSES)),
            ("recherches", f"Avis de recherche ({len(RECHERCHES)})", _grid_panel(RECHERCHES)),
        ]
        panels.append(("moves", "Déplacements", _moves_panel()))
        for key, label, panel in panels:
            btn = QPushButton(label)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _=False, k=key: self._switch_page_tab(k))
            tabs_row.addWidget(btn)
            self._page_tab_btns[key] = btn
            self._page_panels[key] = panel
            content.addWidget(panel, 1)
        tabs_row.addStretch()
        lay.addLayout(tabs_row)
        lay.addLayout(content, 1)
        self._switch_page_tab("donjons")

    def _switch_page_tab(self, key):
        for k, panel in self._page_panels.items():
            panel.setVisible(k == key)
        active = (f"QPushButton {{ background:{ACC}22; color:{TEXT}; border:1px solid {ACC}; "
                  f"border-radius:7px; padding:6px 14px; font-size:12px; font-weight:700; }}")
        inactive = (f"QPushButton {{ background:transparent; color:{MUT}; border:1px solid {BORDER}; "
                    f"border-radius:7px; padding:6px 14px; font-size:12px; }}"
                    f"QPushButton:hover {{ color:{TEXT}; border-color:{ACC}; }}")
        for k, btn in self._page_tab_btns.items():
            btn.setStyleSheet(active if k == key else inactive)

    def _view_general(self, path):
        dlg = ImageViewerDialog(path, self)
        dlg.exec()

    def _open_boss(self, boss):
        existing = self._dialogs.get(boss["key"])
        if existing is not None:
            existing.raise_()
            existing.activateWindow()
            return
        dlg = BossNotesDialog(self.config, boss, self)
        dlg.destroyed.connect(lambda _=None, k=boss["key"]: self._dialogs.pop(k, None))
        self._dialogs[boss["key"]] = dlg
        dlg.show()
