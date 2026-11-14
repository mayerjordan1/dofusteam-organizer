"""Fenêtre flottante PNJ : recherche, favoris, packs, convoi, copie de commande dans le presse-papiers.

Sans bordure, toujours au-dessus, redimensionnable (les cartes se recomposent en grille), déplaçable, opacité et thème
réglables, position et taille mémorisées. Elle ne fait que COPIER du texte : aucune frappe n'est envoyée au jeu.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer, QMimeData, pyqtSignal, QEvent
from PyQt6.QtGui import QDrag, QPixmap
from PyQt6.QtWidgets import (QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea,
                             QApplication, QMenu, QComboBox, QSlider, QCheckBox, QSizePolicy)

import pnj_data
from pages.pnj_convoi import ConvoiPanel
from pages.pnj_packs import PacksView
from pages.pnj_widgets import (FONT, THEMES, Theme, theme_of, Thumbs, PnjCard, CardGrid, CorrectionDialog,
                               CustomPosDialog, icon_label, skin_pixmap, ICON_POSITION)
from pnj_engine import (COPY_MODES, MODE_LABEL, LANGS, Result, apply_correction, command, search, popular, npc_result)
from pnj_prefs import PnjPrefs

EDGE = 7          # épaisseur de la zone de redimensionnement
MIN_W, MIN_H = 250, 180


class FavSlot(QFrame):
    """Un des 6 emplacements de favoris : clic = copier, glisser-déposer = réordonner, clic droit = vider."""
    dropped = pyqtSignal(int, int)     # source, destination
    clicked = pyqtSignal(int)
    cleared = pyqtSignal(int)

    def __init__(self, idx, fav, th, s, thumbs, label):
        super().__init__()
        self.idx, self.fav, self.th = idx, fav, th
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"QFrame{{background:{th.bg2}; border:1px solid {th.border}; border-radius:{int(10 * s)}px;}}")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(2)
        pic = QLabel()
        size = int(40 * s)
        pic.setFixedSize(size, size)
        pic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pic.setStyleSheet("background:transparent; border:none;")
        pm = None
        if fav:
            if fav.get("kind") == "pack":
                path = pnj_data.image_path(pnj_data.pack_image_rel(fav["pack_icon"])) if fav.get("pack_icon") else None
                pm = QPixmap(str(path)).scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation) if path else skin_pixmap("icon_group.png", size - 6)
            elif fav.get("icon"):
                pm = skin_pixmap(fav["icon"], size - 6)
            elif fav.get("npc_id"):
                pm = thumbs.get(pnj_data.npc_image_rel(fav["npc_id"]), size)
            elif fav.get("kind") == "zaap":
                pm = skin_pixmap("icon_zaap.png", size - 6)
            if pm is None or pm.isNull():
                pm = skin_pixmap("icon_dofusteam.png", size - 10)
        pic.setPixmap(pm) if pm else pic.setText("＋")
        pic.setStyleSheet(f"background:transparent; border:none; color:{th.ghost}; font-size:{int(18 * s)}px;")
        lay.addWidget(pic, 0, Qt.AlignmentFlag.AlignHCenter)
        name = QLabel(f"{idx + 1}  {fav['name']}" if fav else f"{idx + 1}")
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name.setStyleSheet(f"background:transparent; border:none; color:{th.mut}; font-family:{FONT}; font-size:{int(10 * s)}px;")
        name.setMaximumWidth(int(90 * s))
        lay.addWidget(name)
        self.setToolTip(label)
        self._press = None

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.RightButton:
            self.cleared.emit(self.idx)
        else:
            self._press = e.position().toPoint()

    def mouseMoveEvent(self, e):
        if self._press is not None and self.fav and (e.position().toPoint() - self._press).manhattanLength() > 8:
            drag = QDrag(self)
            mime = QMimeData()
            mime.setText(f"pnjfav:{self.idx}")
            drag.setMimeData(mime)
            self._press = None
            drag.exec(Qt.DropAction.MoveAction)

    def mouseReleaseEvent(self, e):
        if self._press is not None and e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.idx)
        self._press = None

    def dragEnterEvent(self, e):
        if e.mimeData().text().startswith("pnjfav:"):
            e.acceptProposedAction()

    def dropEvent(self, e):
        t = e.mimeData().text()
        if t.startswith("pnjfav:"):
            self.dropped.emit(int(t.split(":")[1]), self.idx)
            e.acceptProposedAction()


class PnjOverlay(QWidget):
    toggle_requested = pyqtSignal()          # émis depuis le thread du raccourci global
    hotkey_changed = pyqtSignal(str)
    status_done = pyqtSignal()
    status_sig = pyqtSignal(str)             # messages de la macro convoi (thread -> interface)

    def __init__(self, config, logic=None):
        super().__init__(None)
        self.config, self.logic = config, logic
        self.prefs = PnjPrefs(config)
        self.data = pnj_data.load_pnj()
        self.packs = pnj_data.load_packs()
        self.thumbs = Thumbs()
        self.thumbs.loaded.connect(self._on_thumb)
        self.results: list = []
        self.sel = 0
        self._cards: list = []
        self._copied = ""
        self._edge = None
        self._scale = 1.0
        self._view = "home"            # home | settings | convoi
        self._pack_view = None
        self._open_pack_id = None
        self._geo_mode = "full"       # géométrie mémorisée séparément : fenêtre complète / pack discret
        self._convoi = None
        self.setWindowTitle("PNJ — DofusTeam")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.setMinimumSize(MIN_W, MIN_H)
        self.toggle_requested.connect(self.toggle)
        self.status_sig.connect(self._toast)
        self.status_done.connect(self._convoi_finished)
        self._convoi_running = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(EDGE, EDGE, EDGE, EDGE)
        self.root = QFrame()
        self.root.setObjectName("PnjRoot")
        self.root.setMouseTracking(True)
        outer.addWidget(self.root)
        self.root_lay = QVBoxLayout(self.root)
        self.root_lay.setContentsMargins(10, 8, 10, 8)
        self.root_lay.setSpacing(8)

        self._rescale_timer = QTimer(self)
        self._rescale_timer.setSingleShot(True)
        self._rescale_timer.timeout.connect(self._rebuild)
        self._toast_timer = QTimer(self)
        self._toast_timer.setSingleShot(True)
        self._toast_timer.timeout.connect(self._clear_toast)

        g = self.prefs["geometry"]
        if g and len(g) == 4:
            self.setGeometry(*g)
        else:
            self.resize(560, 640)
        self.setWindowOpacity(max(30, min(100, self.prefs["opacity"])) / 100)
        self._build()

    # ── infos dérivées ─────────────────────────────────────────────────────────
    @property
    def th(self) -> Theme:
        return theme_of(self.prefs["theme"])

    def _is_compact(self) -> bool:
        """Pack discret : un pack est ouvert, sans recherche en cours ni autre vue."""
        return bool(self._open_pack_id) and self.prefs["compact"] and self._view == "home" and not getattr(self, "_query", "")

    def _calc_scale(self):
        if self._is_compact():
            return round(max(0.75, min(1.5, self.width() / 400)) * 10) / 10
        return round(max(0.8, min(1.6, self.width() / 560)) * 10) / 10

    def _mode_label(self):
        return MODE_LABEL[self.prefs["mode"]]

    def _lbl_style(self, size, color=None, bold=False):
        return (f"background:transparent; border:none; color:{color or self.th.text}; font-family:{FONT}; "
                f"font-size:{int(size * self._scale)}px; font-weight:{700 if bold else 400};")

    # ── construction ───────────────────────────────────────────────────────────
    def _build(self):
        self._scale = self._calc_scale()
        th, s = self.th, self._scale
        while self.root_lay.count():
            it = self.root_lay.takeAt(0)
            w_ = it.widget()
            if w_:
                w_.hide(); w_.setParent(None); w_.deleteLater()
        self.root.setStyleSheet(f"QFrame#PnjRoot{{background:{th.bg}; border:1px solid {th.border}; border-radius:{int(14 * s)}px;}}")

        # En-tête (zone de déplacement)
        self.header = QWidget()
        self.header.setStyleSheet("background:transparent;")
        h = QHBoxLayout(self.header)
        h.setContentsMargins(0, 0, 0, 0)
        compact = self._is_compact()
        h.addWidget(icon_label("icon_dofusteam.png", int(22 * s)))
        title = QLabel(self._open_pack_title() if compact else "PNJ")
        title.setStyleSheet(self._lbl_style(14 if compact else 15, th.text, True))
        title.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)   # se tronque quand la fenêtre est étroite
        title.setToolTip(title.text())
        if not compact:
            title.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        h.addWidget(title, 1 if compact else 0)
        h.addStretch()
        self.header.setToolTip("Glisser pour déplacer · molette pour régler l'opacité")
        views = () if compact else (("Convoi", "convoi", "Déplacer plusieurs personnages"), ("Réglages", "settings", "Thème, opacité, langue"))
        if compact:
            more = QPushButton("⋯")
            more.setCursor(Qt.CursorShape.PointingHandCursor)
            more.setToolTip("Menu du pack")
            more.setFixedSize(int(26 * s), int(22 * s))
            more.setStyleSheet(f"QPushButton{{background:{th.bg3}; color:{th.text}; border:1px solid {th.border}; border-radius:7px; "
                               f"font-size:{int(13 * s)}px;}}QPushButton:hover{{border-color:{th.acc};}}")
            more.clicked.connect(lambda: self._compact_menu(more))
            h.addWidget(more)
        for text, view, tip in views:
            b = QPushButton(text)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setToolTip(tip)
            on = self._view == view
            b.setStyleSheet(f"QPushButton{{background:{th.bg3 if not on else th.acc}; color:{th.text if not on else th.bg}; "
                            f"border:1px solid {th.border}; border-radius:8px; padding:3px 10px; font-family:{FONT}; font-size:{int(11 * s)}px;}}")
            b.clicked.connect(lambda _=False, v=view: self._set_view(v))
            ic = icon_label({"convoi": "icon_group.png", "settings": "icon_settings.png"}[view], int(16 * s))
            h.addWidget(ic)
            h.addWidget(b)
        close = QPushButton("✕")
        close.setFlat(True)
        close.setFixedSize(int(24 * s), int(24 * s))
        close.setStyleSheet(f"QPushButton{{background:transparent; color:{th.mut}; border:none; font-size:{int(14 * s)}px;}}"
                            f"QPushButton:hover{{color:{th.acc};}}")
        close.clicked.connect(self.hide)
        h.addWidget(close)
        self.header.installEventFilter(self)
        self.root_lay.addWidget(self.header)

        # Recherche + mode de copie (mode discret : recherche cachée, bouton de mode dans l'en-tête)
        bar = QHBoxLayout()
        self.search = QLineEdit(getattr(self, "_query", ""))
        self.search.setPlaceholderText("PNJ, zone, « zaap astrub », 4,-18…")
        self.search.setStyleSheet(f"QLineEdit{{background:{th.bg2}; color:{th.text}; border:1px solid {th.border}; "
                                  f"border-radius:{int(8 * s)}px; padding:{int(6 * s)}px {int(10 * s)}px; "
                                  f"font-family:{FONT}; font-size:{int(13 * s)}px;}}QLineEdit:focus{{border-color:{th.acc};}}")
        self.search.textChanged.connect(self._on_query)
        self.search.installEventFilter(self)
        bar.addWidget(self.search, 1)
        self.mode_btn = QPushButton(self._mode_label())
        self.mode_btn.setToolTip("Mode de copie (Tab)")
        self.mode_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mode_btn.setStyleSheet(f"QPushButton{{background:{th.bg3}; color:{th.acc}; border:1px solid {th.border}; "
                                    f"border-radius:{int(8 * s)}px; padding:{int(6 * s)}px {int(12 * s)}px; font-family:{FONT}; "
                                    f"font-size:{int(12 * s)}px; font-weight:700;}}")
        self.mode_btn.clicked.connect(self.cycle_mode)
        if compact:
            self.search.setParent(self.root)
            self.search.hide()
        else:
            bar.addWidget(self.mode_btn)
            bw = QWidget()
            bw.setLayout(bar)
            self.root_lay.addWidget(bw)

        # Corps défilant
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet(f"QScrollArea{{background:transparent; border:none;}} QScrollArea > QWidget > QWidget{{background:transparent;}}"
                                  f"QScrollBar:vertical{{background:transparent; width:6px;}} QScrollBar::handle:vertical{{background:{th.bg4}; border-radius:3px;}}"
                                  f"QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;}}")
        self.body = QWidget()
        self.body_lay = QVBoxLayout(self.body)
        self.body_lay.setContentsMargins(0, 0, 0, 0)
        self.body_lay.setSpacing(int(10 * s))
        self.scroll.setWidget(self.body)
        self.root_lay.addWidget(self.scroll, 1)

        self.toast = QLabel("")
        self.toast.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.toast.setStyleSheet(self._lbl_style(11, th.acc))
        self.root_lay.addWidget(self.toast)
        self.toast.setVisible(not compact)
        self._apply_min_size(compact)
        self._fill_body()

    def _section(self, text):
        l = QLabel(text.upper())
        l.setStyleSheet(self._lbl_style(10, self.th.mut) + "letter-spacing:1px;")
        return l

    def _fill_body(self):
        while self.body_lay.count():
            it = self.body_lay.takeAt(0)
            w_ = it.widget()
            if w_ is not None and w_ is self._convoi:
                w_.hide(); w_.setParent(None)      # le panneau convoi garde son état : on le détache sans le détruire
            elif w_:
                w_.hide(); w_.setParent(None); w_.deleteLater()
        self._cards = []
        if self.data is None:
            self.body_lay.addWidget(self._section("Données PNJ indisponibles — connecte-toi une fois pour les télécharger."))
            self.body_lay.addStretch()
            return
        if self._view == "settings":
            return self._fill_settings()
        if self._view == "convoi":
            return self._fill_convoi()
        compact = self._is_compact()
        if not compact:
            self.body_lay.addWidget(self._favs_widget())
        q = self.search.text().strip()
        if q:
            self.results = search(q, self.data, self.prefs["lang"])
            self.sel = min(self.sel, max(0, len(self.results) - 1))
            self.body_lay.addWidget(self._section(f"Résultats ({len(self.results)})"))
            if not self.results:
                self.body_lay.addWidget(self._section("Aucun résultat. Seuls les PNJ de quête localisés sont connus."))
            self.body_lay.addWidget(self._grid(self.results))
        else:
            self.results = []
            self._pack_view = PacksView(self.prefs, self.th, self.thumbs, self.data, self.packs, self.prefs["lang"],
                                        self._scale, self.prefs["mode"], self.prefs["anti_lag"], self._open_pack_id, compact)
            self._pack_view.compact_requested.connect(self._enter_compact)
            self._pack_view.pack_opened.connect(self._on_pack_opened)
            self._pack_view.favs_changed.connect(self._fill_body)
            self._pack_view.copy_requested.connect(self._activate if compact else self.copy_result)
            self._pack_view.card_menu.connect(self._card_menu)
            self.body_lay.addWidget(self._pack_view)
            if not compact:
                self.body_lay.addWidget(self._custom_positions())
                self.body_lay.addWidget(self._section("Les plus cités"))
                self.body_lay.addWidget(self._grid(popular(self.data, self.prefs["lang"], 6)))
        self.body_lay.addStretch()

    # ── cartes ─────────────────────────────────────────────────────────────────
    def _resolve(self, r: Result) -> Result:
        return apply_correction(r, self.prefs.correction(r.key), self.data.zaaps)

    def _grid(self, results):
        grid = CardGrid(int(330 * self._scale))
        cards = []
        favkeys = {f["key"] for f in self.prefs["favs"] if f}
        for i, r0 in enumerate(results):
            r = self._resolve(r0)
            card = PnjCard(r, self.th, self._scale, self.thumbs, command(r, self.prefs["mode"], self.prefs["anti_lag"]),
                           self._mode_label(), is_fav=r0.key in favkeys, corrected=bool(self.prefs.correction(r0.key)))
            card.copy_requested.connect(self.copy_result)
            card.fav_toggled.connect(self._toggle_fav)
            card.menu_requested.connect(self._card_menu)
            card.selected.connect(lambda _r, c=card: self._select_card(c))
            cards.append(card)
            self._cards.append(card)
        if cards and self.search.text().strip():
            cards[min(self.sel, len(cards) - 1)].set_selected(True)
        grid.set_items(cards)
        return grid

    def _select_card(self, card):
        for c in self._cards:
            c.set_selected(c is card)

    def _card_menu(self, r: Result, pos):
        base = next((x for x in self.results if x.key == r.key), r)
        m = QMenu(self)
        m.addAction("Copier").triggered.connect(lambda: self.copy_result(r))
        m.addAction("Ajouter aux favoris").triggered.connect(lambda: self._toggle_fav(r))
        m.addAction("Corriger la position / le zaap…").triggered.connect(lambda: self._correct(base, r))
        if self.prefs.correction(r.key):
            m.addAction("Revenir à l'original").triggered.connect(lambda: self._reset_correction(r))
        m.addAction("Envoyer au convoi").triggered.connect(lambda: self._to_convoi(r))
        if r.npc_id:
            m.addAction("Ajouter à un pack…").triggered.connect(lambda: self._add_to_pack(r.npc_id))
            cp = next((c for c in self.prefs["custom_packs"] if c["id"] == self._open_pack_id), None)
            if cp and r.npc_id in cp["npcs"] and not self.search.text().strip():
                m.addAction("Retirer de ce pack").triggered.connect(lambda: self._remove_from_pack(cp, r.npc_id))
        m.exec(pos)

    def _convoi_finished(self):
        self._convoi_running = False
        self._toast_timer.start(4000)

    def _clear_toast(self):
        self.toast.setText("")
        if self._is_compact() and not self._convoi_running:
            self.toast.setVisible(False)

    # ── clic sur une tuile : lance le convoi (ou copie) ────────────────────────
    def _activate(self, r: Result):
        conv = self.prefs["convoi"]
        if conv.get("click_launches") and self.logic is not None:
            self._launch_convoi(r)
        else:
            self.copy_result(r)

    def _launch_convoi(self, r: Result):
        if self._convoi_running:
            self._toast("Un convoi est déjà en cours (Échap pour l'arrêter)")
            return
        try:
            import pnj_convoi_macro
        except Exception as e:  # noqa: BLE001
            self._toast(f"Macro indisponible : {e}")
            return
        r = self._resolve(r) if r.key.startswith("pnj:") else r
        self._convoi_running = True
        self.toast.setVisible(True)
        ok = pnj_convoi_macro.run_convoi(self.config, self.logic, r, self.prefs["convoi"],
                                         on_status=self.status_sig.emit, on_done=lambda: self.status_done.emit())
        if not ok:
            self._convoi_running = False

    # ── mode pack discret ──────────────────────────────────────────────────────
    def _apply_min_size(self, compact):
        """Mode discret : jamais plus petit que 2 PNJ (une tuile de large, deux de haut). Largeur libre au-delà."""
        if compact:
            s = self._scale
            tile_w, tile_h = int(86 * s), int((44 + 56) * s)
            self.setMinimumSize(tile_w + 2 * EDGE + 20, int(40 * s) + 2 * tile_h + 6 + 2 * EDGE + 56)
        else:
            self.setMinimumSize(MIN_W, MIN_H)

    def _compact_menu(self, anchor):
        m = QMenu(self)
        m.addAction(f"Mode de copie : {self._mode_label()} (changer)").triggered.connect(self.cycle_mode)
        a = m.addAction("Un clic lance le convoi (sinon : copie)")
        a.setCheckable(True)
        a.setChecked(bool(self.prefs["convoi"].get("click_launches")))
        a.triggered.connect(lambda v: (self.prefs["convoi"].__setitem__("click_launches", bool(v)), self.prefs.save(), self._fill_body()))
        m.addAction("Fenêtre complète").triggered.connect(self._leave_compact)
        m.addAction("Retour aux packs").triggered.connect(self._close_pack)
        m.addAction("Masquer").triggered.connect(self.hide)
        m.exec(anchor.mapToGlobal(anchor.rect().bottomLeft()))

    def _open_pack_title(self) -> str:
        from pages.pnj_packs import _pack_name
        lang = self.prefs["lang"]
        for p in self.packs:
            if p["id"] == self._open_pack_id:
                return _pack_name(p, lang)
        for c in self.prefs["custom_packs"]:
            if c["id"] == self._open_pack_id:
                return c["name"]
        return "Pack"

    def _on_pack_opened(self, pid):
        self._open_pack_id = pid
        if pid:
            self.prefs["compact"] = True       # cliquer un pack = l'overlay devient ce pack
        QTimer.singleShot(0, self._sync_mode)

    def _enter_compact(self):
        self.prefs["compact"] = True
        QTimer.singleShot(0, self._sync_mode)

    def _leave_compact(self):
        self.prefs["compact"] = False
        QTimer.singleShot(0, self._sync_mode)

    def _close_pack(self):
        self._open_pack_id = None
        QTimer.singleShot(0, self._sync_mode)

    def _sync_mode(self):
        """Passe de la fenêtre complète au pack discret (et inversement) en mémorisant la taille/position de chacun."""
        new = "compact" if self._is_compact() else "full"
        if new != self._geo_mode:
            self._write_geometry()
            self._geo_mode = new
            g = self.prefs["geometry_compact" if new == "compact" else "geometry"]
            if g and len(g) == 4:
                self.setGeometry(*g)
            elif new == "compact":
                self.setGeometry(self.x(), self.y(), 340, 460)
            else:
                self.setGeometry(self.x(), self.y(), 560, 640)
        self.prefs.save()
        self._build()

    # ── packs perso : ajouter / retirer un PNJ, épingler un pack en favori ──
    def _add_to_pack(self, npc_id):
        from PyQt6.QtWidgets import QInputDialog
        packs = self.prefs["custom_packs"]
        new_label = "＋ Nouveau pack…"
        pick, ok = QInputDialog.getItem(self, "Ajouter à un pack", "Pack", [c["name"] for c in packs] + [new_label], 0, False)
        if not ok:
            return
        if pick == new_label:
            name, ok = QInputDialog.getText(self, "Nouveau pack", "Nom du pack")
            if not ok or not name.strip():
                return
            pack = {"id": f"perso-{max([int(c['id'].split('-')[1]) for c in packs if c['id'].startswith('perso-') and c['id'].split('-')[1].isdigit()] + [0]) + 1}",
                    "name": name.strip(), "npcs": []}
            packs.append(pack)
        else:
            pack = next(c for c in packs if c["name"] == pick)
        if npc_id not in pack["npcs"]:
            pack["npcs"].append(npc_id)
        self.prefs.save()
        self._toast(f"Ajouté à « {pack['name']} »")
        self._fill_body()

    def _remove_from_pack(self, pack, npc_id):
        if npc_id in pack["npcs"]:
            pack["npcs"].remove(npc_id)
            self.prefs.save()
            self._fill_body()

    def _open_pack(self, pid):
        """Ouvre un pack (depuis un favori) : vide la recherche et affiche la liste du pack."""
        self._open_pack_id = pid
        self._view = "home"
        self._query = ""
        self.prefs["compact"] = True
        self._sync_mode()

    def _original(self, r: Result) -> Result:
        """Carte sans correction locale (pour comparer et pour « revenir à l'original »)."""
        if r.key.startswith("pnj:") and r.npc_id:
            from pnj_engine import _pnj_result
            n = self.data.npc(r.npc_id)
            i = int(r.key.split(":")[2])
            if n and i < len(n["p"]):
                return _pnj_result(self.data, n, i, self.prefs["lang"])
        return r

    def _correct(self, base: Result, shown: Result):
        dlg = CorrectionDialog(self._original(shown), self.th, self)
        if dlg.exec():
            self.prefs.set_correction(shown.key, dlg.result_correction())
            self._fill_body()

    def _reset_correction(self, r):
        self.prefs.set_correction(r.key, None)
        self._fill_body()

    def _on_thumb(self, rel):
        for c in self._cards:
            c.refresh_thumb(rel)
        if self.prefs["favs"] and any(f and f.get("npc_id") and pnj_data.npc_image_rel(f["npc_id"]) == rel for f in self.prefs["favs"]):
            self._rebuild_soon()

    # ── favoris ────────────────────────────────────────────────────────────────
    def _fav_dict(self, r: Result):
        return {"key": r.key, "kind": r.kind, "npc_id": r.npc_id, "name": r.name, "x": r.x, "y": r.y,
                "zaap": [r.zaap.x, r.zaap.y] if r.zaap else None, "sa": r.sa, "icon": getattr(r, "icon", None)}

    def _toggle_fav(self, r: Result):
        favs = self.prefs["favs"]
        for i, f in enumerate(favs):
            if f and f["key"] == r.key:
                favs[i] = None
                break
        else:
            if None in favs:
                favs[favs.index(None)] = self._fav_dict(r)
            else:
                self._toast("6 favoris maximum : clic droit sur un favori pour le retirer")
                return
        self.prefs.save()
        self._fill_body()

    def _favs_widget(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)
        lay.addWidget(self._section("Favoris (1-6 · glisser pour réordonner · clic droit pour vider)"))
        row = QHBoxLayout()
        row.setSpacing(int(6 * self._scale))
        for i, f in enumerate(self.prefs["favs"]):
            slot = FavSlot(i, f, self.th, self._scale, self.thumbs, f["name"] if f else "Emplacement libre")
            slot.clicked.connect(self._copy_fav)
            slot.cleared.connect(self._clear_fav)
            slot.dropped.connect(self._swap_fav)
            row.addWidget(slot, 1)
        lay.addLayout(row)
        return w

    def _fav_result(self, f) -> Result:
        from pnj_engine import Zaap
        z = Zaap(f["zaap"][0], f["zaap"][1], -1) if f.get("zaap") else None
        return Result(key=f["key"], kind=f["kind"], name=f["name"], area="", x=f["x"], y=f["y"], zaap=z,
                      npc_id=f.get("npc_id"), sa=f.get("sa"))

    def _copy_fav(self, i):
        f = self.prefs["favs"][i]
        if f and f.get("kind") == "pack":
            self._open_pack(f["pack_id"])
        elif f:
            self.copy_result(self._fav_result(f))

    def _clear_fav(self, i):
        self.prefs["favs"][i] = None
        self.prefs.save()
        self._fill_body()

    def _swap_fav(self, a, b):
        favs = self.prefs["favs"]
        favs[a], favs[b] = favs[b], favs[a]
        self.prefs.save()
        self._fill_body()

    # ── positions perso ────────────────────────────────────────────────────────
    def _custom_positions(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        head = QHBoxLayout()
        head.addWidget(self._section("Mes positions"), 1)
        add = QPushButton("+ Ajouter")
        add.setCursor(Qt.CursorShape.PointingHandCursor)
        add.setStyleSheet(f"QPushButton{{background:{self.th.bg3}; color:{self.th.text}; border:1px solid {self.th.border}; border-radius:8px; padding:2px 10px; font-family:{FONT}; font-size:{int(11 * self._scale)}px;}}")
        add.clicked.connect(self._add_custom)
        head.addWidget(add)
        hw = QWidget()
        hw.setLayout(head)
        lay.addWidget(hw)
        from pnj_engine import nearest_zaap
        cards = []
        for i, p in enumerate(self.prefs["custom_pos"]):
            r = Result(key=f"perso:{p['id']}", kind="pos", name=p["name"], area="", x=p["x"], y=p["y"],
                       zaap=nearest_zaap(p["x"], p["y"], self.data.zaaps))
            card = PnjCard(r, self.th, self._scale, self.thumbs, command(r, self.prefs["mode"], self.prefs["anti_lag"]),
                           self._mode_label(), icon_override=p.get("icon") or ICON_POSITION)
            card.copy_requested.connect(self.copy_result)
            card.fav_toggled.connect(lambda r, pid=p["id"]: self._del_custom(pid))
            card.star.setText("🗑")
            card.star.setToolTip("Supprimer cette position")
            card.menu_requested.connect(lambda r, pos, p=p: self._edit_custom(p))
            cards.append(card)
        g = CardGrid(int(330 * self._scale))
        g.set_items(cards)
        lay.addWidget(g)
        return w

    def _add_custom(self):
        d = CustomPosDialog(self.th, self)
        if d.exec():
            v = d.value()
            v["id"] = max([p["id"] for p in self.prefs["custom_pos"]] + [0]) + 1
            self.prefs["custom_pos"].append(v)
            self.prefs.save()
            self._fill_body()

    def _edit_custom(self, p):
        d = CustomPosDialog(self.th, self, p)
        if d.exec():
            p.update(d.value())
            self.prefs.save()
            self._fill_body()

    def _del_custom(self, pid):
        self.prefs["custom_pos"] = [p for p in self.prefs["custom_pos"] if p["id"] != pid]
        self.prefs.save()
        self._fill_body()

    # ── réglages ───────────────────────────────────────────────────────────────
    def _fill_settings(self):
        th, s = self.th, self._scale

        def row(label, widget, icon=None):
            w = QWidget()
            l = QHBoxLayout(w)
            l.setContentsMargins(0, 0, 0, 0)
            if icon:
                l.addWidget(icon_label(icon, int(18 * s)))
            lab = QLabel(label)
            lab.setStyleSheet(self._lbl_style(12, th.text))
            l.addWidget(lab)
            l.addStretch()
            l.addWidget(widget)
            return w

        self.body_lay.addWidget(self._section("Réglages"))
        theme = QComboBox()
        for k, t in THEMES.items():
            theme.addItem(t.label, k)
        theme.setCurrentIndex(theme.findData(self.prefs["theme"]))
        theme.currentIndexChanged.connect(lambda: self._set_pref("theme", theme.currentData(), rebuild=True))
        self.body_lay.addWidget(row("Thème", theme))
        op = QSlider(Qt.Orientation.Horizontal)
        op.setRange(30, 100)
        op.setValue(self.prefs["opacity"])
        op.setMinimumWidth(140)
        op.valueChanged.connect(self._set_opacity)
        self.body_lay.addWidget(row("Opacité", op))
        lang = QComboBox()
        for i, c in enumerate(LANGS):
            lang.addItem(c.upper(), i)
        lang.setCurrentIndex(self.prefs["lang"])
        lang.currentIndexChanged.connect(lambda: self._set_pref("lang", lang.currentData(), rebuild=True))
        self.body_lay.addWidget(row("Langue des noms", lang))
        anti = QCheckBox()
        anti.setChecked(self.prefs["anti_lag"])
        anti.toggled.connect(lambda v: self._set_pref("anti_lag", v))
        self.body_lay.addWidget(row("Anti lag (/zaap répété)", anti, "icon_zaap.png"))
        key = QLineEdit(self.config.get("pnj_overlay_key", "f7"))
        key.setFixedWidth(int(90 * s))
        key.setPlaceholderText("ex : f7")
        key.editingFinished.connect(lambda: self._set_hotkey(key.text().strip()))
        self.body_lay.addWidget(row("Raccourci afficher / masquer", key))
        from PyQt6.QtWidgets import QDoubleSpinBox
        conv = self.prefs["convoi"]
        self.body_lay.addWidget(self._section("Convoi (macro) — délais en secondes"))

        def dspin(key, lo, hi):
            sp = QDoubleSpinBox()
            sp.setRange(lo, hi)
            sp.setSingleStep(0.1)
            sp.setDecimals(2)
            sp.setValue(float(conv[key]))
            sp.valueChanged.connect(lambda v, k=key: (conv.__setitem__(k, float(v)), self.prefs.save()))
            return sp
        self.body_lay.addWidget(row("Entre deux persos", dspin("between_delay", 0.1, 3), "icon_zaap.png"))
        self.body_lay.addWidget(row("Attente d'arrivée du chef au zaap", dspin("arrival_delay", 0.5, 20), "icon_zaap.png"))
        self.body_lay.addWidget(row("Attente après le suivi auto", dspin("follow_delay", 0.2, 10)))
        fk = QLineEdit(conv["follow_key"])
        fk.setFixedWidth(int(90 * s))
        fk.editingFinished.connect(lambda: (conv.__setitem__("follow_key", fk.text().strip().lower() or "ctrl+w"), self.prefs.save()))
        self.body_lay.addWidget(row("Touche du suivi automatique", fk))
        ta = QCheckBox()
        ta.setChecked(bool(conv["travel_all"]))
        ta.toggled.connect(lambda v: (conv.__setitem__("travel_all", bool(v)), self.prefs.save()))
        self.body_lay.addWidget(row("/travel sur tous (sinon : chef seul)", ta))
        cl = QCheckBox()
        cl.setChecked(bool(conv["click_launches"]))
        cl.toggled.connect(lambda v: (conv.__setitem__("click_launches", bool(v)), self.prefs.save()))
        self.body_lay.addWidget(row("Un clic sur une tuile lance le convoi", cl))
        info = QLabel("Taille : tire sur les bords de la fenêtre. Position et taille sont mémorisées.")
        info.setWordWrap(True)
        info.setStyleSheet(self._lbl_style(11, th.mut))
        self.body_lay.addWidget(info)
        self.body_lay.addStretch()

    def _set_pref(self, k, v, rebuild=False):
        self.prefs[k] = v
        self.prefs.save()
        if rebuild:
            self._build()
        else:
            self._fill_body()

    def _set_opacity(self, v):
        self.prefs["opacity"] = v
        self.setWindowOpacity(v / 100)
        self.prefs.save()

    def _set_hotkey(self, key):
        self.config.set("pnj_overlay_key", key)
        self.config.save()
        self.hotkey_changed.emit(key)

    # ── convoi ─────────────────────────────────────────────────────────────────
    def _fill_convoi(self):
        if self.logic is None:
            self.body_lay.addWidget(self._section("Convoi indisponible (pas de gestion de fenêtres)."))
            return
        if self._convoi is None:
            self._convoi = ConvoiPanel(self.logic, self.config, self.prefs, self.th, self._scale)
        else:
            self._convoi.th, self._convoi.s = self.th, self._scale
            self._convoi.render()
        self.body_lay.addWidget(self._convoi)
        self._convoi.show()
        self.body_lay.addStretch()

    def _to_convoi(self, r: Result):
        if self._convoi is None and self.logic is not None:
            self._convoi = ConvoiPanel(self.logic, self.config, self.prefs, self.th, self._scale)
        if self._convoi is not None:
            self._convoi.set_target(r)
        self._set_view("convoi")

    def _set_view(self, v):
        self._view = "home" if self._view == v else v
        self._build()

    # ── copie ──────────────────────────────────────────────────────────────────
    def copy_result(self, r: Result):
        r = self._resolve(r) if r.key.startswith("pnj:") else r
        cmd = command(r, self.prefs["mode"], self.prefs["anti_lag"])
        QApplication.clipboard().setText(cmd)
        self._toast(f"Copié : {cmd}")
        if self._is_compact() and self._pack_view is not None:
            for c in getattr(self._pack_view, "_cards", []):
                if getattr(c, "r", None) is not None and c.r.key == r.key and hasattr(c, "flash"):
                    c.flash()

    def _toast(self, text):
        self.toast.setText(text)
        self.toast.setWordWrap(True)
        if self._is_compact():
            self.toast.setVisible(True)          # en mode discret le message n'apparaît que le temps de l'action
        self._toast_timer.start(4000 if self._is_compact() else 2500)

    def cycle_mode(self):
        i = COPY_MODES.index(self.prefs["mode"])
        self.prefs["mode"] = COPY_MODES[(i + 1) % len(COPY_MODES)]
        self.prefs.save()
        self.mode_btn.setText(self._mode_label())
        self._fill_body()

    # ── recherche / clavier ────────────────────────────────────────────────────
    def _on_query(self, _t):
        self._query = self.search.text()
        self.sel = 0
        self._fill_body()

    def eventFilter(self, obj, ev):
        if obj is self.header and ev.type() == QEvent.Type.Wheel:
            step = 5 if ev.angleDelta().y() > 0 else -5
            self._set_opacity(max(30, min(100, self.prefs["opacity"] + step)))
            return True
        if obj is self.header and ev.type() == QEvent.Type.MouseButtonPress and ev.button() == Qt.MouseButton.LeftButton:
            self.windowHandle().startSystemMove()
            return True
        if obj is getattr(self, "search", None) and ev.type() == QEvent.Type.KeyPress:
            k = ev.key()
            if k == Qt.Key.Key_Tab:
                self.cycle_mode()
                return True
            if k in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and self.results:
                self.copy_result(self.results[self.sel])
                return True
            if k in (Qt.Key.Key_Down, Qt.Key.Key_Up) and self.results:
                self.sel = max(0, min(len(self.results) - 1, self.sel + (1 if k == Qt.Key.Key_Down else -1)))
                for i, c in enumerate(self._cards):
                    c.set_selected(i == self.sel)
                return True
            if k == Qt.Key.Key_Escape:
                if self.search.text():
                    self.search.clear()
                else:
                    self.hide()
                return True
            if ev.modifiers() & Qt.KeyboardModifier.ControlModifier and Qt.Key.Key_1 <= k <= Qt.Key.Key_6:
                self._copy_fav(k - Qt.Key.Key_1)
                return True
        return super().eventFilter(obj, ev)

    def keyPressEvent(self, e):
        k = e.key()
        if self._is_compact() and Qt.Key.Key_1 <= k <= Qt.Key.Key_9 and self._pack_view is not None:
            rs = self._pack_view._ordered
            if k - Qt.Key.Key_1 < len(rs):
                self.copy_result(rs[k - Qt.Key.Key_1])    # 1-9 : copie le Nième PNJ du pack
        elif Qt.Key.Key_1 <= k <= Qt.Key.Key_6 and not self.search.hasFocus():
            self._copy_fav(k - Qt.Key.Key_1)      # 1-6 copient le favori quand on ne tape pas dans la recherche
        elif k == Qt.Key.Key_Tab:
            self.cycle_mode()
        elif k == Qt.Key.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(e)

    # ── affichage / géométrie ──────────────────────────────────────────────────
    def toggle(self):
        if self.isVisible():
            self.hide()
        else:
            self.show_overlay()

    def show_overlay(self):
        self.show()
        self.raise_()
        self.activateWindow()
        (self.setFocus if self._is_compact() else self.search.setFocus)()

    def _rebuild_soon(self):
        self._rescale_timer.start(150)

    def _rebuild(self):
        self._build()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if self._calc_scale() != self._scale and hasattr(self, "root_lay"):
            self._rebuild_soon()
        self._save_geometry()

    def moveEvent(self, e):
        super().moveEvent(e)
        self._save_geometry()

    def _save_geometry(self):
        if not hasattr(self, "_geo_timer"):
            self._geo_timer = QTimer(self)
            self._geo_timer.setSingleShot(True)
            self._geo_timer.timeout.connect(self._write_geometry)
        self._geo_timer.start(400)

    def _write_geometry(self):
        g = self.geometry()
        self.prefs["geometry_compact" if self._geo_mode == "compact" else "geometry"] = [g.x(), g.y(), g.width(), g.height()]
        self.prefs.save()

    def closeEvent(self, e):
        self._write_geometry()
        super().closeEvent(e)

    # Redimensionnement par les bords (la fenêtre est sans bordure)
    def _edges_at(self, p):
        r = self.rect()
        e = Qt.Edge(0)
        if p.x() <= EDGE:
            e |= Qt.Edge.LeftEdge
        if p.x() >= r.width() - EDGE:
            e |= Qt.Edge.RightEdge
        if p.y() <= EDGE:
            e |= Qt.Edge.TopEdge
        if p.y() >= r.height() - EDGE:
            e |= Qt.Edge.BottomEdge
        return e

    def mouseMoveEvent(self, e):
        ed = self._edges_at(e.position().toPoint())
        L, R, T, B = Qt.Edge.LeftEdge, Qt.Edge.RightEdge, Qt.Edge.TopEdge, Qt.Edge.BottomEdge
        if ed in (L | T, R | B):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif ed in (R | T, L | B):
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        elif ed in (L, R):
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        elif ed in (T, B):
            self.setCursor(Qt.CursorShape.SizeVerCursor)
        else:
            self.unsetCursor()

    def mousePressEvent(self, e):
        ed = self._edges_at(e.position().toPoint())
        if e.button() == Qt.MouseButton.LeftButton and ed and self.windowHandle():
            self.windowHandle().startSystemResize(ed)
