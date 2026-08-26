"""Page "Zaap" — liste complète des zaaps + favoris (embarquée).

Remplace ZaapFavoritesDialog (zaap_favorites.py) comme point d'entrée pour
consulter/marquer les favoris : la barre flottante (navbar) sert désormais
uniquement à faire un clic droit et valider un favori déjà choisi (macro),
tandis que la gestion complète (recherche + étoile) vit ici, dans l'appli
principale, cohérente avec le reste des pages (Mes équipes, Chasse au
trésor, ...).
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QScrollArea,
)
from PyQt6.QtCore import Qt

from theme import TEXT, MUT, ACC, GOLD, BG2, BORDER, glass_card, section_label, mono, load_icon
from zaap_data import ZAAPS, get_favorites, toggle_favorite

# Largeurs de colonnes partagées entre l'en-tête et chaque ligne, pour que
# Territoire / Région / Coordonnées restent alignées.
_STAR_W = 44
_NAME_W = 220
_REGION_W = 180


def _make_header(title, subtitle):
    header = QWidget()
    header.setObjectName("PageHeader")
    lay = QVBoxLayout(header)
    lay.setContentsMargins(24, 18, 24, 14)
    lay.setSpacing(2)

    title_row = QHBoxLayout()
    title_row.setSpacing(8)
    icon = load_icon("icon_zaap.png", 22)
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


class ZaapMenuPage(QWidget):
    """Recherche + liste complète des zaaps, étoile pour favoris."""

    def __init__(self, config, logic, parent=None):
        super().__init__(parent)
        self.config = config
        self.logic = logic
        self._rows = []
        self._build()
        self._filter()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        lay.addWidget(_make_header(
            "Zaap",
            "Consulte les 42 zaaps et marque tes favoris ⭐ — utilisés ensuite d'un "
            "clic droit sur la barre flottante pour lancer la macro de téléportation.",
        ))

        body = QWidget()
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(24, 18, 24, 18)
        body_lay.setSpacing(12)

        body_lay.addWidget(self._search_row())
        body_lay.addWidget(self._list_card(), 1)

        lay.addWidget(body, 1)

    def _search_row(self):
        row = QWidget()
        row.setStyleSheet("background:transparent;")
        rl = QHBoxLayout(row)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(10)

        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍  Rechercher un zaap ou une région...")
        self.search.textChanged.connect(self._filter)
        rl.addWidget(self.search, 1)

        self.favs_only = QPushButton("★  Favoris uniquement")
        self.favs_only.setCheckable(True)
        self.favs_only.toggled.connect(self._filter)
        self._style_favs_btn()
        self.favs_only.toggled.connect(self._style_favs_btn)
        rl.addWidget(self.favs_only)

        return row

    def _style_favs_btn(self):
        on = self.favs_only.isChecked()
        self.favs_only.setStyleSheet(
            f"background:rgba(200,160,0,0.15);color:{GOLD};border:1px solid rgba(200,160,0,0.35);"
            f"border-radius:6px;padding:6px 14px;font-size:12px;font-weight:700;"
            if on else
            f"background:{BG2};color:{MUT};border:1px solid {BORDER};"
            f"border-radius:6px;padding:6px 14px;font-size:12px;"
        )

    def _column_header(self):
        row = QWidget()
        row.setStyleSheet("background:transparent;")
        rl = QHBoxLayout(row)
        rl.setContentsMargins(12, 0, 22, 0)
        rl.setSpacing(12)

        spacer = QLabel("")
        spacer.setFixedWidth(_STAR_W)
        spacer.setStyleSheet("background:transparent;")
        rl.addWidget(spacer)

        h_territoire = section_label("Territoire")
        h_territoire.setMinimumWidth(_NAME_W)
        rl.addWidget(h_territoire)

        h_region = section_label("Région")
        h_region.setMinimumWidth(_REGION_W)
        rl.addWidget(h_region)

        rl.addStretch()

        rl.addWidget(section_label("Coordonnées"))

        return row

    def _list_card(self):
        c = glass_card(QWidget())
        clay = QVBoxLayout(c)
        clay.setContentsMargins(6, 6, 6, 6)
        clay.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background:transparent;border:none;")

        # L'en-tête de colonnes vit DANS le même widget scrollable que les
        # lignes (plutôt qu'en sibling fixe au-dessus) : ses largeurs de
        # colonnes (_NAME_W/_REGION_W) sont bien plus larges que 700px ne le
        # permet, donc les sortir du scroll forçait la fenêtre entière à
        # s'élargir bien au-delà du minimum déclaré — ici elles défilent
        # simplement à l'horizontale avec les lignes, toujours alignées.
        self.list_w = QWidget()
        self.list_w.setStyleSheet("background:transparent;")
        self.list_l = QVBoxLayout(self.list_w)
        self.list_l.setSpacing(4)
        self.list_l.setContentsMargins(4, 4, 4, 4)
        self.list_l.addWidget(self._column_header())

        self.rows_w = QWidget()
        self.rows_w.setStyleSheet("background:transparent;")
        self.list_l_rows = QVBoxLayout(self.rows_w)
        self.list_l_rows.setContentsMargins(0, 0, 0, 0)
        self.list_l_rows.setSpacing(4)
        self.list_l_rows.addStretch()
        self.list_l.addWidget(self.rows_w)

        scroll.setWidget(self.list_w)
        clay.addWidget(scroll)
        self._scroll = scroll
        return c

    def _filter(self):
        query = self.search.text().strip().lower()
        favs = get_favorites(self.config)
        only_favs = self.favs_only.isChecked()

        items = ZAAPS
        if only_favs:
            items = [z for z in items if z["name"] in favs]
        if query:
            items = [z for z in items if query in z["name"].lower() or query in z["region"].lower()]

        while self.list_l_rows.count() > 1:
            item = self.list_l_rows.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for z in items:
            self.list_l_rows.insertWidget(self.list_l_rows.count() - 1, self._make_row(z, z["name"] in favs))

        if not items:
            empty = QLabel("Aucun zaap ne correspond à cette recherche.")
            empty.setStyleSheet(f"color:{MUT}; font-size:12px; background:transparent; padding:16px;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.list_l_rows.insertWidget(self.list_l_rows.count() - 1, empty)

    def _make_row(self, z, is_fav):
        row = QWidget()
        row.setObjectName(f"ZaapRow{abs(hash(z['name']))}")
        row.setStyleSheet(
            f"QWidget#{row.objectName()} {{ background:{BG2}; border-radius:8px; }}"
            f"QWidget#{row.objectName()}:hover {{ background:#1c2230; }}"
        )
        rl = QHBoxLayout(row)
        rl.setContentsMargins(12, 8, 12, 8)
        rl.setSpacing(12)

        star = QPushButton("★" if is_fav else "☆")
        star.setFixedSize(_STAR_W, 38)
        star.setCursor(Qt.CursorShape.PointingHandCursor)
        star.setToolTip("Retirer des favoris" if is_fav else "Ajouter aux favoris")
        star.setStyleSheet(
            f"background:rgba(200,160,0,0.15);color:{GOLD};border:1px solid rgba(200,160,0,0.3);"
            f"border-radius:6px;font-size:19px;"
            if is_fav else
            f"background:transparent;color:{MUT};border:1px solid {BORDER};border-radius:6px;font-size:19px;"
        )
        star.clicked.connect(lambda _, n=z["name"]: self._toggle(n))
        rl.addWidget(star)

        name_lbl = QLabel(z["name"])
        name_lbl.setStyleSheet(f"color:{TEXT}; font-size:13px; font-weight:600; background:transparent; border:none;")
        name_lbl.setMinimumWidth(_NAME_W)
        rl.addWidget(name_lbl)

        reg_lbl = QLabel(z["region"])
        reg_lbl.setStyleSheet(f"color:{MUT}; font-size:11px; background:transparent; border:none;")
        reg_lbl.setMinimumWidth(_REGION_W)
        rl.addWidget(reg_lbl)

        rl.addStretch()

        coord_row = QHBoxLayout()
        coord_row.setSpacing(4)
        pin = QLabel("📍")
        pin.setStyleSheet("background:transparent; border:none; font-size:11px;")
        coord_row.addWidget(pin)
        coord_lbl = QLabel(f"[{z['coords'][0]},{z['coords'][1]}]")
        coord_lbl.setFont(mono(10))
        coord_lbl.setStyleSheet(f"color:{ACC}; background:transparent; border:none;")
        coord_row.addWidget(coord_lbl)
        rl.addLayout(coord_row)

        return row

    def _toggle(self, name):
        toggle_favorite(self.config, name)
        self._filter()
