"""Packs de PNJ : liste de packs (illustrés par leur Dofus), détail dans l'ordre de jeu avec case « fait », packs perso.

Les packs officiels viennent de pnj-packs.json (site) ; les packs perso restent en local (pnj_prefs).
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QCheckBox, QInputDialog,
                             QComboBox)

import pnj_data
from pages.pnj_widgets import COMPACT_TILE_W, FONT, Theme, Thumbs, PnjCard, CompactTile, CardGrid, skin_pixmap
from pnj_engine import PnjData, npc_result, command, apply_correction


def _pack_name(p, lang):
    n = p.get("n") or [p.get("name", "")]
    return (n[lang] if lang < len(n) else "") or n[0]


class PacksView(QWidget):
    copy_requested = pyqtSignal(object)
    card_menu = pyqtSignal(object, object)
    favs_changed = pyqtSignal()
    compact_requested = pyqtSignal()
    pack_opened = pyqtSignal(object)     # id du pack ouvert (ou None) : l'overlay le retient d'une reconstruction à l'autre

    def __init__(self, prefs, th: Theme, thumbs: Thumbs, data: PnjData, packs: list, lang: int, scale: float,
                 mode: str, anti_lag: bool, open_id=None, compact=False, parent=None):
        super().__init__(parent)
        self.prefs, self.th, self.thumbs, self.data = prefs, th, thumbs, data
        self.packs, self.lang, self.s, self.mode, self.anti_lag = packs, lang, scale, mode, anti_lag
        self.open_id = open_id
        self.compact = compact
        self._ordered: list = []
        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(0, 0, 0, 0)
        self.lay.setSpacing(int(8 * scale))
        self._cards: list = []
        self.render()

    # ── helpers ──
    def _all_packs(self):
        out = [dict(p, _custom=False) for p in self.packs]
        for c in self.prefs["custom_packs"]:
            out.append({"id": c["id"], "n": [c["name"]], "icon": None, "npcs": c["npcs"], "quests": [],
                        "missing": {}, "_custom": True})
        return out

    def _clear(self):
        while self.lay.count():
            it = self.lay.takeAt(0)
            w_ = it.widget()
            if w_:
                w_.hide(); w_.setParent(None); w_.deleteLater()
        self._cards = []

    def _btn(self, text, fn):
        b = QPushButton(text)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.setStyleSheet(f"QPushButton{{background:{self.th.bg3}; color:{self.th.text}; border:1px solid {self.th.border}; "
                        f"border-radius:8px; padding:4px 12px; font-family:{FONT}; font-size:{int(12 * self.s)}px;}}"
                        f"QPushButton:hover{{border-color:{self.th.acc};}}")
        b.clicked.connect(fn)
        return b

    def _title(self, text):
        t = QLabel(text)
        t.setStyleSheet(f"color:{self.th.mut}; font-family:{FONT}; font-size:{int(11 * self.s)}px; letter-spacing:1px; background:transparent;")
        return t

    # ── liste ──
    def render(self):
        self._clear()
        if self.open_id:
            return self._render_pack()
        head = QHBoxLayout()
        head.addWidget(self._title("PACKS"))
        head.addStretch()
        head.addWidget(self._btn("+ Pack perso", self._new_pack))
        head.addWidget(self._btn("+ Pack d'une zone", self._new_zone_pack))
        w = QWidget()
        w.setLayout(head)
        self.lay.addWidget(w)
        packs = self._all_packs()
        if not packs:
            self.lay.addWidget(self._title("Aucun pack disponible (données non téléchargées)."))
        for p in packs:
            self.lay.addWidget(self._pack_row(p))

    def _pack_row(self, p):
        th, s = self.th, self.s
        row = QFrame()
        row.setCursor(Qt.CursorShape.PointingHandCursor)
        row.setStyleSheet(f"QFrame{{background:{th.bg2}; border:1px solid {th.border}; border-radius:{int(12 * s)}px;}}"
                          f"QFrame:hover{{border-color:{th.acc};}}")
        lay = QHBoxLayout(row)
        lay.setContentsMargins(int(10 * s), int(8 * s), int(10 * s), int(8 * s))
        ico = QLabel()
        size = int(44 * s)
        ico.setFixedSize(size, size)
        pm = None
        if p.get("icon"):
            path = pnj_data.image_path(pnj_data.pack_image_rel(p["icon"]))
            if path:
                from PyQt6.QtGui import QPixmap
                pm = QPixmap(str(path)).scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        ico.setPixmap(pm if pm and not pm.isNull() else skin_pixmap("icon_group.png", size - 8))
        ico.setStyleSheet("background:transparent; border:none;")
        lay.addWidget(ico)
        col = QVBoxLayout()
        name = QLabel(_pack_name(p, self.lang))
        name.setStyleSheet(f"color:{th.text}; font-family:{FONT}; font-size:{int(14 * s)}px; font-weight:700; background:transparent; border:none;")
        nq = len(p.get("quests") or [])
        sub = QLabel((f"{nq} quêtes · " if nq else "") + f"{len(p['npcs'])} PNJ" + (" · perso" if p["_custom"] else ""))
        sub.setStyleSheet(f"color:{th.mut}; font-family:{FONT}; font-size:{int(11 * s)}px; background:transparent; border:none;")
        col.addWidget(name)
        col.addWidget(sub)
        lay.addLayout(col, 1)
        row.mousePressEvent = lambda e, pid=p["id"]: self._open(pid)
        return row

    def _open(self, pid):
        self.open_id = pid
        self.pack_opened.emit(pid)
        self.render()

    # ── détail d'un pack ──
    def _render_pack(self):
        p = next((x for x in self._all_packs() if x["id"] == self.open_id), None)
        if not p:
            self.open_id = None
            return self.render()
        self._ordered = []
        head = QHBoxLayout()
        head.addWidget(self._btn("← Packs", self._close))
        t = QLabel(_pack_name(p, self.lang))
        t.setStyleSheet(f"color:{self.th.text}; font-family:{FONT}; font-size:{int(15 * self.s)}px; font-weight:700; background:transparent;")
        head.addWidget(t, 1)
        is_fav = any(f and f.get("pack_id") == p["id"] for f in self.prefs["favs"])
        head.addWidget(self._btn("★ Favori" if is_fav else "☆ Favori", lambda: self._toggle_pack_fav(p)))
        head.addWidget(self._btn("Tout décocher", lambda: (self.prefs.reset_done(p["id"]), self.render())))
        if p["_custom"]:
            head.addWidget(self._btn("Supprimer", lambda: self._delete(p["id"])))
        if not self.compact:
            head.addWidget(self._btn("Mode discret", self.compact_requested.emit))
            w = QWidget()
            w.setLayout(head)
            self.lay.addWidget(w)

        items = []
        if self.compact:
            return self._render_tiles(p)
        for i, nid in enumerate(p["npcs"]):
            r = npc_result(self.data, nid, self.lang)
            if r is None:
                items.append(self._missing_row(p, nid, i))
                continue
            r = apply_correction(r, self.prefs.correction(r.key), self.data.zaaps)
            cnt = (p.get("counts") or {}).get(str(nid))
            chk = QCheckBox(f"{i + 1}" + ((f"·{cnt}×" if self.compact else f" · vu {cnt}×") if cnt else ""))
            chk.setToolTip(f"Vu {cnt} fois dans les quêtes du pack" if cnt else "Fait")
            chk.setChecked(self.prefs.is_done(p["id"], nid))
            chk.setStyleSheet(f"QCheckBox{{color:{self.th.mut}; font-family:{FONT}; font-size:{int(12 * self.s)}px; background:transparent;}}")
            chk.toggled.connect(lambda v, pid=p["id"], n=nid: self.prefs.set_done(pid, n, v))
            self._ordered.append(r)
            if True:
                card = PnjCard(r, self.th, self.s, self.thumbs, command(r, self.mode, self.anti_lag), self._mode_label(),
                               corrected=bool(self.prefs.correction(r.key)), left_widget=chk)
                card.star.hide()
            card.copy_requested.connect(self.copy_requested)
            card.menu_requested.connect(self.card_menu)
            self._cards.append(card)
            items.append(card)
        grid = CardGrid(int(330 * self.s))
        grid.set_items(items)
        self.lay.addWidget(grid)

    def _render_tiles(self, p):
        """Mode discret : une tuile par PNJ (icône + position dessous), qui se recompose selon la largeur."""
        tiles = []
        for nid in p["npcs"]:
            r = npc_result(self.data, nid, self.lang)
            cnt = (p.get("counts") or {}).get(str(nid))
            if r is None:
                info = (p.get("missing") or {}).get(str(nid)) or {}
                names = info.get("n") or [f"PNJ #{nid}"]
                place = info.get("in") or []
                nm = names[self.lang] if self.lang < len(names) else names[0]
                pl = (place[self.lang] if self.lang < len(place) else place[0]) if place else "position inconnue"
                from pnj_engine import Result
                ghost = Result(key=f"missing:{nid}", kind="pnj", name=nm, area="", x=0, y=0, zaap=None, npc_id=nid)
                tiles.append(CompactTile(ghost, self.th, self.s, self.thumbs, "", f"{nm}\nÀ l'intérieur : {pl}",
                                         no_position=True, label_override="donjon"))
                continue
            r = apply_correction(r, self.prefs.correction(r.key), self.data.zaaps)
            self._ordered.append(r)
            cmd = command(r, self.mode, self.anti_lag)
            tip = f"{r.name} — {r.area}\n{cmd}" + (f"\nVu {cnt} fois" if cnt else "")
            t = CompactTile(r, self.th, self.s, self.thumbs, cmd, tip, corrected=bool(self.prefs.correction(r.key)))
            t.copy_requested.connect(self.copy_requested)
            t.menu_requested.connect(self.card_menu)
            self._cards.append(t)
            tiles.append(t)
        grid = CardGrid(int(COMPACT_TILE_W * self.s), int(6 * self.s), center=True)
        grid.set_items(tiles)
        self._tile_widgets = tiles
        self.lay.addWidget(grid)

    def _mode_label(self):
        from pnj_engine import MODE_LABEL
        return MODE_LABEL[self.mode]

    def _missing_row(self, p, nid, i):
        """PNJ sans position utilisable (ex. dans un donjon) : nom + lieu, pas de bouton de copie."""
        info = (p.get("missing") or {}).get(str(nid)) or {}
        names = info.get("n") or [f"PNJ #{nid}"]
        place = info.get("in") or []
        f = QFrame()
        f.setStyleSheet(f"QFrame{{background:{self.th.bg2}; border:1px dashed {self.th.border}; border-radius:{int(12 * self.s)}px;}}")
        lay = QVBoxLayout(f)
        if self.compact:
            lay.setContentsMargins(8, 4, 8, 4)
            lay.setSpacing(0)
        a = QLabel(f"{i + 1}. " + (names[self.lang] if self.lang < len(names) else names[0]))
        a.setStyleSheet(f"color:{self.th.text}; font-family:{FONT}; font-size:{int(13 * self.s)}px; font-weight:600; background:transparent; border:none;")
        b = QLabel(("À l'intérieur : " + (place[self.lang] if self.lang < len(place) else place[0])) if place else "Position inconnue")
        b.setStyleSheet(f"color:{self.th.mut}; font-family:{FONT}; font-size:{int(11 * self.s)}px; background:transparent; border:none;")
        lay.addWidget(a)
        lay.addWidget(b)
        return f

    def _close(self):
        self.open_id = None
        self.pack_opened.emit(None)
        self.render()

    # ── packs perso ──
    def _new_pack(self):
        name, ok = QInputDialog.getText(self, "Pack perso", "Nom du pack")
        if ok and name.strip():
            self.prefs["custom_packs"].append({"id": f"perso-{len(self.prefs['custom_packs']) + 1}-{abs(hash(name)) % 9999}",
                                               "name": name.strip(), "npcs": []})
            self.prefs.save()
            self.render()

    def _new_zone_pack(self):
        zones = sorted(((self.data.area_name(sa, self.lang), sa) for sa in {int(k) for k in self.data.areas}), key=lambda t: t[0])
        names = [z for z, _ in zones]
        pick, ok = QInputDialog.getItem(self, "Pack d'une zone", "Zone", names, 0, False)
        if not ok:
            return
        sa = dict(zones)[pick]
        npcs = [n["id"] for n in self.data.npcs if n["p"] and n["p"][0][2] == sa]
        npcs.sort(key=lambda i: -self.data.npc(i).get("w", 0))
        if not npcs:
            return
        self.prefs["custom_packs"].append({"id": f"zone-{sa}", "name": pick, "npcs": npcs})
        self.prefs.save()
        self.render()

    def _toggle_pack_fav(self, p):
        """Épingle / retire le pack dans les 6 favoris (un clic sur le favori ouvre le pack)."""
        favs = self.prefs["favs"]
        for i, f in enumerate(favs):
            if f and f.get("pack_id") == p["id"]:
                favs[i] = None
                break
        else:
            if None not in favs:
                return
            favs[favs.index(None)] = {"key": f"pack:{p['id']}", "kind": "pack", "pack_id": p["id"], "npc_id": None,
                                      "name": _pack_name(p, self.lang), "x": 0, "y": 0, "zaap": None, "sa": None,
                                      "icon": None, "pack_icon": p.get("icon")}
        self.prefs.save()
        self.favs_changed.emit()

    def _delete(self, pid):
        self.prefs["custom_packs"] = [c for c in self.prefs["custom_packs"] if c["id"] != pid]
        self.prefs.save()
        self.open_id = None
        self.render()
