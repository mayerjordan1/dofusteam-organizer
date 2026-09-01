"""Page "Donjons" — fiches boss avec indications clé à garder sous la main.

Chaque boss ouvre une popup en 2 parties :
- Guide : contenu riche en lecture seule (titres colorés, emphases, images
  intégrées au fil du texte et cliquables pour zoomer) — curé à l'avance
  (par moi/Claude, à partir des liens/screens fournis) et stocké tel quel en
  HTML dans config["boss_guide_html"][boss_key]. Pensé pour être lu EN JEU,
  d'un coup d'œil, pendant un tour compté — donc les images importantes sont
  affichées en taille lisible directement, pas juste en vignette.
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
        self.resize(520, 700)
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

        # ── Guide (riche, lecture seule, curé à l'avance) ───────────────
        guide_html = self.config.get("boss_guide_html", {}).get(self.boss["key"], "")
        if guide_html:
            guide_title = QLabel("Guide")
            guide_title.setStyleSheet(f"color:{MUT}; font-size:10px; font-weight:700; letter-spacing:1px; background:transparent; border:none;")
            cl.addWidget(guide_title)

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
            cl.addWidget(self.guide, 3)

        # ── Mes notes (texte libre, éditable) ───────────────────────────
        notes_title = QLabel("Mes notes")
        notes_title.setStyleSheet(f"color:{MUT}; font-size:10px; font-weight:700; letter-spacing:1px; background:transparent; border:none;")
        cl.addWidget(notes_title)

        self.notes = QTextEdit()
        self.notes.setPlaceholderText("Rappels personnels rapides, en plus du Guide ci-dessus...")
        self.notes.setStyleSheet(
            f"QTextEdit {{ background:{BG2}; color:{TEXT}; border:1px solid {BORDER}; "
            f"border-radius:8px; padding:10px; font-size:12px; }}"
        )
        notes = self.config.get("boss_notes", {})
        self.notes.setPlainText(notes.get(self.boss["key"], ""))
        # Sans Guide, les notes perso deviennent le contenu principal — leur
        # donner tout l'espace disponible plutôt qu'une petite bande basse.
        cl.addWidget(self.notes, 1 if guide_html else 3)

        # ── Galerie d'images en vrac ─────────────────────────────────────
        img_row = QHBoxLayout()
        img_title = QLabel("Autres images")
        img_title.setStyleSheet(f"color:{MUT}; font-size:10px; font-weight:700; letter-spacing:1px; background:transparent; border:none;")
        img_row.addWidget(img_title)
        img_row.addStretch()
        img_row.addWidget(ghost_btn("📋  Coller", self._paste_image))
        img_row.addWidget(ghost_btn("📁  Ajouter", self._add_image_file))
        cl.addLayout(img_row)

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
        cl.addWidget(self._strip_scroll)

        self._empty_hint = QLabel("Aucune image — colle une capture (Ctrl+C dans le jeu) ou ajoute un fichier.")
        self._empty_hint.setStyleSheet(f"color:{MUT}; font-size:10.5px; background:transparent; border:none;")
        cl.addWidget(self._empty_hint)

        self._refresh_images()

        btns = QHBoxLayout()
        if self.boss.get("url"):
            link = QLabel(f'<a href="{self.boss["url"]}" style="color:{ACC};">🔗 Guide complet (dofuspourlesnoobs.com)</a>')
            link.setStyleSheet("background:transparent; border:none; font-size:11px;")
            link.setOpenExternalLinks(True)
            btns.addWidget(link)
        btns.addStretch()
        btns.addWidget(ghost_btn("Fermer", self.close))
        cl.addLayout(btns)

        lay.addWidget(content, 1)

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
            path = _boss_img_dir(self.boss["key"]) / raw[len("zoom:"):]
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

        body = QWidget()
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(24, 18, 24, 18)
        body_lay.setSpacing(12)

        # Référence générale (pas liée à un boss précis) — un seul petit
        # bouton discret, pas un pavé qui prendrait de la place dans la page.
        general_path = _boss_img_dir("_general") / "deplacement.png"
        if general_path.exists():
            ref_row = QHBoxLayout()
            ref_row.addWidget(ghost_btn("📍  États de déplacement", lambda: self._view_general(general_path)))
            ref_row.addStretch()
            body_lay.addLayout(ref_row)

        grid = QWidget()
        grid.setStyleSheet("background:transparent;")
        grid_lay = QGridLayout(grid)
        grid_lay.setContentsMargins(0, 0, 0, 0)
        grid_lay.setSpacing(14)
        grid_lay.setAlignment(Qt.AlignmentFlag.AlignLeft)

        for i, boss in enumerate(BOSSES):
            tile = BossCard(boss)
            tile.clicked.connect(lambda b=boss: self._open_boss(b))
            grid_lay.addWidget(tile, i // GRID_COLS, i % GRID_COLS)

        body_lay.addWidget(grid)
        body_lay.addStretch()

        lay.addWidget(body, 1)

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
