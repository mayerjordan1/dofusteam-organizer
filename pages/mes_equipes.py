"""Page "Mes équipes" — presets rapides, ordre d'initiative, actions de fenêtre.

Réutilise la logique métier existante (DofusLogic.apply_preset/sort_taskbar,
ScanThread, PresetEditor, InviteDialog) sans réécriture — cette page assemble
des widgets autour d'elle, tout le calcul reste dans main.py/dofus_logic.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QScrollArea, QApplication,
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QMimeData, QTimer
from PyQt6.QtGui import QIcon, QDrag

from theme import TEXT, MUT, BG, BG2, BG3, ACC, GREEN, GOLD, BORDER, section_label, glass_card, accent_btn, ghost_btn, make_avatar, ClickableAvatar, crown_icon

MAX_SLOTS = 8
CARD_W, CARD_H = 84, 100
AVATAR_SIZE = 60


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


class TeamSlotCard(QWidget):
    """Une position dans l'ordre d'initiative (config["custom_order"]), affichée
    dans une seule ligne de 8. Volontairement distincte de AccountRow (qui reste
    la ligne détaillée avec actions ▲▼/équipe/suppr) — ici un aperçu minimal :
    numéro, avatar avec pastille en ligne, nom. Élection du chef : la tuile
    n'a plus de bouton dédié — elle passe en mode « sélection » (armé depuis
    le bouton « Définir le chef » du panneau Groupe) et un clic dessus émet
    sig_leader ; un badge couronne (crown_icon) marque la tuile du chef actuel."""

    sig_leader = pyqtSignal(str)
    sig_reorder = pyqtSignal(str, str, bool)  # (nom glissé, nom cible, insérer après) — direct, sans passer par un preset

    def __init__(self, name, classe, pos_num, config=None, live=False, is_leader=False, parent=None):
        super().__init__(parent)
        self.name = name
        self.classe = classe
        self.config = config
        self.is_leader = is_leader
        self._select_mode = False
        self._press_pos = None
        self.setAcceptDrops(True)
        self.setFixedSize(CARD_W, CARD_H)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(2, 0, 2, 0)
        lay.setSpacing(3)

        num = QLabel(str(pos_num))
        num.setAlignment(Qt.AlignmentFlag.AlignCenter)
        num.setStyleSheet(f"color:{MUT}; font-size:11px; font-weight:700; background:transparent;")
        self.num_lbl = num
        lay.addWidget(num)

        stack = QWidget()
        stack.setFixedSize(AVATAR_SIZE, AVATAR_SIZE)
        av = ClickableAvatar(stack)
        av.setGeometry(0, 0, AVATAR_SIZE, AVATAR_SIZE)
        av.setAlignment(Qt.AlignmentFlag.AlignCenter)
        av.setStyleSheet(f"background:{BG3}; border-radius:{AVATAR_SIZE//2}px;")
        if self.config is not None:
            av.setCursor(Qt.CursorShape.PointingHandCursor)
            av.setToolTip("Clique pour changer le sexe de l'icône")
            av.clicked.connect(self._on_avatar_click)
        self.av = av
        self._refresh_avatar()

        dot = QLabel(stack)
        dot.setGeometry(AVATAR_SIZE - 14, AVATAR_SIZE - 14, 12, 12)
        dot.setStyleSheet(
            f"background:{GREEN if live else '#3a4152'}; border-radius:6px; border:2px solid {BG};"
        )

        if is_leader:
            crown = QLabel(stack)
            crown.setPixmap(crown_icon(16, GOLD))
            crown.setGeometry(-3, -3, 18, 18)
            crown.setStyleSheet("background:transparent;")
            crown.setToolTip("Chef de groupe")

        av_row = QHBoxLayout()
        av_row.addStretch()
        av_row.addWidget(stack)
        av_row.addStretch()
        lay.addLayout(av_row)

        name_lbl = QLabel()
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_lbl.setStyleSheet(f"color:{TEXT}; font-size:11.5px; font-weight:600; background:transparent;")
        fm = name_lbl.fontMetrics()
        name_lbl.setText(fm.elidedText(name, Qt.TextElideMode.ElideRight, CARD_W))
        lay.addWidget(name_lbl)

    def set_pos_num(self, n):
        self.num_lbl.setText(str(n))

    def _refresh_avatar(self):
        sexe = self.config.get("sexes",{}).get(self.name,"h") if self.config is not None else "h"
        pix = make_avatar(self.classe or "", AVATAR_SIZE - 6, sexe)
        if pix:
            self.av.setPixmap(pix)
        else:
            self.av.setText("?")
            self.av.setStyleSheet(f"color:{MUT}; font-size:20px; background:transparent;")

    def _toggle_sexe(self):
        sexes = self.config.get("sexes",{})
        sexes[self.name] = "f" if sexes.get(self.name,"h")=="h" else "h"
        self.config.set("sexes",sexes); self.config.save()
        self._refresh_avatar()

    def _on_avatar_click(self):
        if self._select_mode:
            self.sig_leader.emit(self.name)
        else:
            self._toggle_sexe()

    def mousePressEvent(self, e):
        if self._select_mode and e.button() == Qt.MouseButton.LeftButton:
            self.sig_leader.emit(self.name)
            return
        if e.button() == Qt.MouseButton.LeftButton:
            self._press_pos = e.position().toPoint()
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._select_mode or self._press_pos is None or not (e.buttons() & Qt.MouseButton.LeftButton):
            super().mouseMoveEvent(e)
            return
        if (e.position().toPoint() - self._press_pos).manhattanLength() < QApplication.startDragDistance():
            super().mouseMoveEvent(e)
            return
        drag = QDrag(self)
        mime = QMimeData()
        mime.setText(self.name)
        drag.setMimeData(mime)
        drag.setPixmap(self.grab())
        drag.setHotSpot(e.position().toPoint())
        self._press_pos = None
        drag.exec(Qt.DropAction.MoveAction)

    def dragEnterEvent(self, e):
        if self._select_mode:
            return
        if e.mimeData().hasText() and e.mimeData().text() != self.name:
            e.acceptProposedAction()
            self.setStyleSheet(f"TeamSlotCard {{ background:rgba(255,138,30,0.1); border:2px solid {ACC}; border-radius:8px; }}")

    def dragMoveEvent(self, e):
        if self._select_mode:
            return
        src = e.mimeData().text() if e.mimeData().hasText() else ""
        if not src or src == self.name:
            return
        # Pas de déplacement live des tuiles ici : dragMoveEvent est appelé
        # DEPUIS la boucle imbriquée de QDrag.exec(), et reparenter des widgets
        # dans le QGridLayout à ce moment-là (même différé d'un QTimer.singleShot(0),
        # qui tourne quand même dans cette même boucle imbriquée) corrompt l'état
        # drag/drop de Qt : le drop finit par être silencieusement annulé et la
        # tuile revient à sa place d'origine au relâchement. Le réordonnancement
        # réel se fait uniquement dans dropEvent, une fois la boucle terminée.
        e.acceptProposedAction()

    def dragLeaveEvent(self, e):
        self.set_select_mode(self._select_mode)

    def dropEvent(self, e):
        self.set_select_mode(self._select_mode)
        src = e.mimeData().text()
        if src and src != self.name:
            after = e.position().x() > self.width() / 2
            self.sig_reorder.emit(src, self.name, after)
        e.acceptProposedAction()

    def set_select_mode(self, on):
        self._select_mode = on
        self.setCursor(Qt.CursorShape.PointingHandCursor if on else Qt.CursorShape.ArrowCursor)
        # Sélecteur de classe (TeamSlotCard { ... }) plutôt qu'une déclaration
        # nue : une déclaration sans sélecteur s'applique aussi à tous les
        # enfants (labels, avatar...) et faisait apparaître plein de petits
        # pointillés orange sur chaque sous-widget de la tuile.
        self.setStyleSheet(
            f"TeamSlotCard {{ background:rgba(255,138,30,0.08); border:1px dashed {ACC}; border-radius:8px; }}"
            if on else
            "TeamSlotCard { background:transparent; border:none; }"
        )


class _EmptySlot(QWidget):
    def __init__(self, pos_num, parent=None):
        super().__init__(parent)
        self.setFixedSize(CARD_W, CARD_H)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(2, 0, 2, 0)
        lay.setSpacing(3)
        num = QLabel(str(pos_num))
        num.setAlignment(Qt.AlignmentFlag.AlignCenter)
        num.setStyleSheet(f"color:{MUT}; font-size:11px; font-weight:700; background:transparent;")
        lay.addWidget(num)
        circle = QLabel("+")
        circle.setFixedSize(AVATAR_SIZE, AVATAR_SIZE)
        circle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        circle.setStyleSheet(
            f"color:{MUT}; font-size:18px; background:transparent; border:1px dashed {BORDER}; border-radius:{AVATAR_SIZE//2}px;"
        )
        row = QHBoxLayout(); row.addStretch(); row.addWidget(circle); row.addStretch()
        lay.addLayout(row)
        lay.addStretch()


class _PresetPill(QPushButton):
    def __init__(self, name, subtitle, active=False, icon_pix=None, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setText(f"{name}\n{subtitle}" if subtitle else name)
        if icon_pix:
            self.setIcon(QIcon(icon_pix))
            self.setIconSize(QSize(22, 22))
        border = f"2px solid {ACC}" if active else f"1px solid {BORDER}"
        fg = TEXT if active else MUT
        self.setStyleSheet(
            f"QPushButton {{ background:{BG2}; color:{fg}; border:none; border-bottom:{border};"
            f"border-radius:0px; padding:6px 16px; font-size:12px; font-weight:700; text-align:left; }}"
            f"QPushButton:hover {{ color:{ACC}; }}"
        )


class MesEquipesPage(QWidget):
    """Page principale — presets rapides + ordre d'initiative + actions de fenêtre."""

    # Émis quand l'ordre des persos change (preset appliqué, ordre d'initiative
    # modifié) — MainWindow s'y connecte pour rafraîchir la bande d'avatars de la
    # mini-toolbar, qui n'est sinon reconstruite qu'après un scan de fenêtres.
    order_changed = pyqtSignal()

    def __init__(self, config, logic, parent=None):
        super().__init__(parent)
        self.config = config
        self.logic = logic
        self._scan_thread = None
        self._select_mode = False
        self._slot_cards = []
        self._slot_widgets = {}
        self._committed_order = []
        self._build()
        self.refresh()

    # ── construction ────────────────────────────────────────────────────
    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        lay.addWidget(_make_header(
            "Mes équipes",
            "Applique un preset, vérifie l'ordre d'initiative et gère tes fenêtres Dofus.",
        ))

        body = QWidget()
        body.setStyleSheet("background:transparent;")
        body_lay = QHBoxLayout(body)
        body_lay.setContentsMargins(24, 18, 24, 18)
        body_lay.setSpacing(16)

        body_lay.addWidget(self._build_left(), stretch=1)
        body_lay.addWidget(self._build_right(), stretch=0, alignment=Qt.AlignmentFlag.AlignTop)

        lay.addWidget(body, stretch=1)

    def _build_left(self):
        left = QWidget()
        left.setStyleSheet("background:transparent;")
        llay = QVBoxLayout(left)
        llay.setContentsMargins(0, 0, 0, 0)
        llay.setSpacing(18)

        # Presets compacts en onglets (pills horizontales)
        llay.addWidget(section_label("Presets"))
        pills_scroll = QScrollArea()
        pills_scroll.setWidgetResizable(True)
        pills_scroll.setFixedHeight(46)
        pills_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        pills_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        pills_container = QWidget()
        self.pills_lay = QHBoxLayout(pills_container)
        self.pills_lay.setContentsMargins(2, 2, 2, 2)
        self.pills_lay.setSpacing(8)
        pills_scroll.setWidget(pills_container)
        llay.addWidget(pills_scroll)

        # Ordre d'initiative
        order_header = QHBoxLayout()
        order_header.setSpacing(6)
        order_header.addWidget(section_label("Ordre d'initiative"))
        info = QLabel("ⓘ")
        info.setStyleSheet(f"color:{MUT};font-size:11px;background:transparent;")
        info.setToolTip("Ordre dans lequel les personnages sont ciblés au tour par tour (touches Suivant/Précédent).")
        order_header.addWidget(info)
        order_header.addStretch()
        order_header.addWidget(ghost_btn("✏ Modifier l'ordre", self._edit_order))
        llay.addLayout(order_header)

        # 2 lignes de 4 — tient dans la largeur minimale de la fenêtre sans
        # scroll horizontal (CARD_W=84 * 4 + espacements reste confortable).
        slots_container = QWidget()
        slots_container.setStyleSheet("background:transparent;")
        self.slots_lay = QGridLayout(slots_container)
        self.slots_lay.setContentsMargins(2, 2, 2, 2)
        self.slots_lay.setSpacing(10)
        llay.addWidget(slots_container)

        llay.addStretch()
        return left

    def _build_right(self):
        right = QWidget()
        right.setFixedWidth(220)
        right.setStyleSheet("background:transparent;")
        rlay = QVBoxLayout(right)
        rlay.setContentsMargins(0, 0, 0, 0)
        rlay.setSpacing(16)

        rlay.addWidget(self._window_card())
        rlay.addWidget(self._group_card())
        rlay.addStretch()
        return right

    def _window_card(self):
        c = glass_card(QWidget())
        clay = QVBoxLayout(c)
        clay.setContentsMargins(16, 14, 16, 14)
        clay.setSpacing(10)

        clay.addWidget(section_label("🖥 Fenêtre"))
        clay.addWidget(ghost_btn("🔍 Scanner les fenêtres", self._scan))
        clay.addWidget(ghost_btn("📊 Trier la barre Windows", self._sort_taskbar))

        self.status_lbl = QLabel("—")
        self.status_lbl.setWordWrap(True)
        self.status_lbl.setStyleSheet(f"color:{MUT}; font-size:11px; background:transparent;")
        clay.addWidget(self.status_lbl)

        return c

    def _group_card(self):
        c = glass_card(QWidget())
        clay = QVBoxLayout(c)
        clay.setContentsMargins(16, 14, 16, 14)
        clay.setSpacing(10)

        clay.addWidget(section_label("👥 Groupe"))
        clay.addWidget(accent_btn("Invitation de groupe", self._open_invite, icon_file="icon_group.png"))

        self.chef_btn = ghost_btn("👑 Définir le chef", self._arm_leader_select)
        clay.addWidget(self.chef_btn)

        self.leader_row = QWidget()
        lr = QHBoxLayout(self.leader_row)
        lr.setContentsMargins(4, 2, 4, 2)
        lr.setSpacing(8)

        self.leader_av = ClickableAvatar()
        self.leader_av.setFixedSize(26, 26)
        self.leader_av.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.leader_av.setStyleSheet(f"background:{BG3}; border-radius:13px;")
        lr.addWidget(self.leader_av)

        self.leader_crown = QLabel()
        self.leader_crown.setFixedSize(14, 14)
        self.leader_crown.setStyleSheet("background:transparent;")
        lr.addWidget(self.leader_crown)

        self.leader_name_lbl = QLabel("Aucun chef désigné")
        self.leader_name_lbl.setStyleSheet(f"color:{MUT}; font-size:11.5px; font-weight:600; background:transparent;")
        lr.addWidget(self.leader_name_lbl, stretch=1)

        clay.addWidget(self.leader_row)

        return c

    # ── rafraîchissement ────────────────────────────────────────────────
    def refresh(self):
        self._refresh_pills()
        self._refresh_slots()
        self._refresh_status()
        self._refresh_leader_display()

    def _refresh_pills(self):
        while self.pills_lay.count():
            item = self.pills_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        presets = self.config.get("presets", [])
        if not presets:
            empty = QLabel("Aucun preset — crée-en un via « Modifier l'ordre ».")
            empty.setStyleSheet(f"color:{MUT}; font-size:11px; background:transparent;")
            self.pills_lay.addWidget(empty)
        else:
            classes = self.config.get("classes", {})
            for i, p in enumerate(presets):
                p_order = p.get("order", [])
                subtitle = f"{len(p_order)} position(s)"
                icon_pix = make_avatar(classes.get(p_order[0], ""), 22) if p_order else None
                pill = _PresetPill(p.get("name", "?"), subtitle, active=(i == 0), icon_pix=icon_pix)
                pill.clicked.connect(lambda _, pp=p: self._apply_preset(pp))
                self.pills_lay.addWidget(pill)
        self.pills_lay.addStretch()

    def _refresh_slots(self):
        while self.slots_lay.count():
            item = self.slots_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._slot_cards = []
        self._slot_widgets = {}
        order = self.config.get("custom_order", [])
        self._committed_order = list(order)
        classes = self.config.get("classes", {})
        live_names = {a.get("name") for a in (self.logic.all_accounts or []) if a.get("hwnd")}
        leader_name = self.config.get("leader_name", "")
        for i in range(MAX_SLOTS):
            if i < len(order):
                name = order[i]
                slot = TeamSlotCard(name, classes.get(name, ""), i + 1, self.config,
                                     live=name in live_names, is_leader=(name == leader_name))
                slot.sig_leader.connect(self._set_leader)
                slot.sig_reorder.connect(self._on_slot_reorder)
                slot.set_select_mode(self._select_mode)
                self.slots_lay.addWidget(slot, i // 4, i % 4)
                self._slot_cards.append(slot)
                self._slot_widgets[name] = slot
            else:
                self.slots_lay.addWidget(_EmptySlot(i + 1), i // 4, i % 4)

    def _refresh_status(self):
        order = self.config.get("custom_order", [])
        live = len([a for a in (self.logic.all_accounts or []) if a.get("hwnd")])
        self.status_lbl.setText(f"{len(order)} compte(s) configuré(s) · {live} fenêtre(s) détectée(s)")

    def _refresh_leader_display(self):
        name = self.config.get("leader_name", "")
        if not name:
            self.leader_av.clear()
            self.leader_av.setStyleSheet(f"background:{BG3}; border-radius:13px;")
            self.leader_crown.clear()
            self.leader_name_lbl.setText("Aucun chef désigné")
            self.leader_name_lbl.setStyleSheet(f"color:{MUT}; font-size:11.5px; font-weight:600; background:transparent;")
            return
        classes = self.config.get("classes", {})
        sexe = self.config.get("sexes", {}).get(name, "h")
        pix = make_avatar(classes.get(name, ""), 24, sexe)
        if pix:
            self.leader_av.setPixmap(pix)
        self.leader_crown.setPixmap(crown_icon(14, GOLD))
        self.leader_name_lbl.setText(name)
        self.leader_name_lbl.setStyleSheet(f"color:{TEXT}; font-size:11.5px; font-weight:600; background:transparent;")

    # ── actions ─────────────────────────────────────────────────────────
    def _apply_preset(self, preset):
        self.logic.apply_preset(preset.get("order", []))
        self.refresh()
        self.order_changed.emit()

    def _insert_order(self, src_name, dst_name, after):
        """Calcule l'ordre résultant d'un déplacement de src_name juste avant/après
        dst_name (insertion, pas un échange)."""
        order = list(self._committed_order)
        if src_name not in order or dst_name not in order:
            return None
        order.remove(src_name)
        idx = order.index(dst_name)
        order.insert(idx + 1 if after else idx, src_name)
        return order

    def _on_slot_reorder(self, src_name, dst_name, after):
        """Glisser-déposer direct dans la grille — insère src_name juste avant/
        après dst_name dans custom_order sans passer par un preset nommé
        (contrairement à « Modifier l'ordre », qui crée toujours un preset). Ne
        trie pas la barre des tâches Windows automatiquement (ça resterait
        perturbant à chaque glissement) — le bouton « Trier la barre Windows »
        reste disponible pour ça séparément."""
        order = self._insert_order(src_name, dst_name, after)
        if order is None:
            return
        self.config.set("custom_order", order)
        self.config.save()
        if self.logic.all_accounts:
            self.logic.all_accounts.sort(
                key=lambda a: order.index(a["name"]) if a.get("name") in order else len(order)
            )
        # Report différé (au tour suivant de la boucle d'événements) : la boucle
        # imbriquée de QDrag.exec() (démarrée depuis mouseMoveEvent de la tuile
        # source) est encore active à ce stade (on est appelé depuis dropEvent) —
        # détruire/recréer les tuiles maintenant (refresh -> _refresh_slots)
        # perturbe l'état interne de drag/grab de Qt et bloquait tout glisser-
        # déposer suivant tant que la page n'était pas rechargée.
        QTimer.singleShot(0, self._after_reorder)

    def _after_reorder(self):
        self.refresh()
        self.order_changed.emit()

    def _arm_leader_select(self):
        self._select_mode = not self._select_mode
        for slot in self._slot_cards:
            slot.set_select_mode(self._select_mode)
        if self._select_mode:
            self.chef_btn.setText("👑 Clique un personnage…")
            self.chef_btn.setStyleSheet(
                f"background:rgba(255,138,30,0.15); color:{ACC}; border:1px solid rgba(255,138,30,0.35);"
                f"border-radius:6px; padding:5px 12px; font-size:12px; font-weight:700;"
            )
        else:
            self.chef_btn.setText("👑 Définir le chef")
            self.chef_btn.setStyleSheet(
                f"background:transparent; color:{MUT}; border:1px solid {BORDER};"
                f"border-radius:6px; padding:5px 12px; font-size:12px;"
            )

    def _set_leader(self, name):
        self.logic.set_leader(name)
        self._select_mode = False
        self.chef_btn.setText("👑 Définir le chef")
        self.chef_btn.setStyleSheet(
            f"background:transparent; color:{MUT}; border:1px solid {BORDER};"
            f"border-radius:6px; padding:5px 12px; font-size:12px;"
        )
        self.refresh()

    def _edit_order(self):
        from main import PresetEditor  # import tardif — évite le cycle pages<->main
        editor = PresetEditor(self.config, -1, self)
        editor.saved.connect(self.refresh)
        editor.exec()

    def _scan(self):
        from main import ScanThread  # import tardif — évite le cycle pages<->main
        self.status_lbl.setText("Scan en cours…")

        def on_done(accounts):
            lv = len(accounts)
            if lv > 0:
                self.status_lbl.setText(f"✅  {lv} fenêtre(s) Dofus détectée(s)")
            else:
                self.status_lbl.setText("⚠  Aucune fenêtre Dofus — Dofus est-il ouvert ?")
            self.refresh()
            # Un perso déconnecté disparaît de logic.all_accounts après le scan
            # (scan_slots() ne renvoie que les fenêtres encore ouvertes) — sans
            # ça, la bande d'avatars de la mini-toolbar n'était reconstruite
            # qu'après un scan lancé depuis la page Gestion, pas depuis ici.
            self.order_changed.emit()

        self._scan_thread = ScanThread(self.logic)
        self._scan_thread.done.connect(on_done)
        self._scan_thread.start()

    def _sort_taskbar(self):
        self.logic.sort_taskbar()

    def _open_invite(self):
        from invite_dialog import InviteDialog  # import tardif — évite le cycle pages<->main
        InviteDialog(self.config, self.logic, self).exec()
