"""Capture des prix de l'HDV : cadre de viseur posé sur le jeu + animation de validation.

Le cadre est une fenêtre transparente toujours au premier plan : seul son contour est cliquable (déplacer, redimensionner),
l'intérieur laisse passer les clics vers le jeu. La zone cadrée est lue à la demande (raccourci) ou automatiquement quand
elle change puis se stabilise. L'image part vers la page « Contribution au marché » du site (voir hdv_bridge.py), qui lit
les prix ; le résultat revient ici sous forme d'une petite animation (icône, coche, prix).

Lecture passive de l'écran uniquement : aucune action n'est envoyée au jeu.
"""
import time, urllib.request

from PyQt6.QtCore import (Qt, QObject, QRect, QPoint, QPointF, QTimer, QByteArray, QBuffer, QIODevice, QVariantAnimation,
                          QPropertyAnimation, QEasingCurve, pyqtSignal, QThread)
from PyQt6.QtGui import QPainter, QColor, QPen, QRegion, QPixmap, QImage, QFont, QPainterPath
from PyQt6.QtWidgets import QWidget, QApplication, QLabel, QHBoxLayout, QVBoxLayout

from theme import BG2, BG3, ACC, GREEN, RED, GOLD, TEXT, MUT, mono
from hdv_bridge import HdvBridge

HB = 9            # épaisseur de la bande de saisie autour de la zone lue
CORNER = 26       # taille des coins (zone de redimensionnement)
MIN_W, MIN_H = 140, 70
STATE_COLORS = {"idle": ACC, "reading": GOLD, "ok": GREEN, "warn": "#fb923c", "off": MUT}


# ── Cadre de viseur ───────────────────────────────────────────────────────────
class CaptureFrame(QWidget):
    geometry_settled = pyqtSignal()
    moved_or_resized = pyqtSignal()

    def __init__(self):
        super().__init__(None)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
                            | Qt.WindowType.Tool | Qt.WindowType.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setMouseTracking(True)
        self.setMinimumSize(MIN_W + 2 * HB, MIN_H + 2 * HB)
        self.state = "off"
        self.base_state = "off"      # état affiché hors animation : "off" (arrêté) ou "idle" (capture en cours)
        self._mode = None
        self._press_global = QPoint()
        self._press_geo = QRect()
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self.geometry_settled.emit)
        self._reset_state_timer = QTimer(self)
        self._reset_state_timer.setSingleShot(True)
        self._reset_state_timer.timeout.connect(lambda: self.set_state(self.base_state))

    # Zone réellement lue (coordonnées d'écran)
    def capture_rect(self):
        g = self.geometry()
        return QRect(g.x() + HB, g.y() + HB, g.width() - 2 * HB, g.height() - 2 * HB)

    def set_capture_rect(self, r):
        self.setGeometry(r.x() - HB, r.y() - HB, r.width() + 2 * HB, r.height() + 2 * HB)

    def set_state(self, state, hold_ms=0):
        self.state = state
        self.update()
        if hold_ms:
            self._reset_state_timer.start(hold_ms)

    # Seule la bande extérieure reçoit la souris ; l'intérieur laisse passer les clics vers le jeu
    def _update_mask(self):
        full = QRegion(self.rect())
        inner = QRegion(self.rect().adjusted(HB, HB, -HB, -HB))
        self.setMask(full.subtracted(inner))

    def resizeEvent(self, e):
        self._update_mask()
        self.moved_or_resized.emit()
        super().resizeEvent(e)

    def moveEvent(self, e):
        self.moved_or_resized.emit()
        super().moveEvent(e)

    def set_base_state(self, state):
        self.base_state = state
        self.set_state(state)

    def showEvent(self, e):
        self._update_mask()
        super().showEvent(e)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        col = QColor(STATE_COLORS.get(self.state, ACC))
        w, h = self.width(), self.height()
        # Bande de saisie très discrète
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(255, 255, 255, 18))
        p.drawRect(0, 0, w, h)
        # Filet autour de la zone lue
        pen = QPen(QColor(col.red(), col.green(), col.blue(), 150), 1)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRect(HB, HB, w - 2 * HB - 1, h - 2 * HB - 1)
        # Coins de viseur
        pen = QPen(col, 3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        L = 22
        for (x, y, dx, dy) in ((2, 2, 1, 1), (w - 3, 2, -1, 1), (2, h - 3, 1, -1), (w - 3, h - 3, -1, -1)):
            p.drawLine(x, y, x + dx * L, y)
            p.drawLine(x, y, x, y + dy * L)
        p.end()

    # ── Déplacement / redimensionnement par la bande ──────────────────────────
    def _hit(self, pos):
        w, h = self.width(), self.height()
        left, right = pos.x() < CORNER, pos.x() > w - CORNER
        top, bottom = pos.y() < CORNER, pos.y() > h - CORNER
        if left and top: return "tl"
        if right and top: return "tr"
        if left and bottom: return "bl"
        if right and bottom: return "br"
        return "move"

    def mouseMoveEvent(self, e):
        if self._mode is None:
            m = self._hit(e.position().toPoint())
            self.setCursor({"tl": Qt.CursorShape.SizeFDiagCursor, "br": Qt.CursorShape.SizeFDiagCursor,
                            "tr": Qt.CursorShape.SizeBDiagCursor, "bl": Qt.CursorShape.SizeBDiagCursor}.get(m, Qt.CursorShape.SizeAllCursor))
            return
        d = e.globalPosition().toPoint() - self._press_global
        g = QRect(self._press_geo)
        if self._mode == "move":
            g.translate(d)
        else:
            if "l" in self._mode: g.setLeft(min(g.left() + d.x(), g.right() - self.minimumWidth()))
            if "r" in self._mode: g.setRight(max(g.right() + d.x(), g.left() + self.minimumWidth()))
            if "t" in self._mode: g.setTop(min(g.top() + d.y(), g.bottom() - self.minimumHeight()))
            if "b" in self._mode: g.setBottom(max(g.bottom() + d.y(), g.top() + self.minimumHeight()))
        self.setGeometry(g)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._mode = self._hit(e.position().toPoint())
            self._press_global = e.globalPosition().toPoint()
            self._press_geo = self.geometry()

    def mouseReleaseEvent(self, _):
        if self._mode:
            self._mode = None
            self._save_timer.start(300)


# ── Animation de validation ───────────────────────────────────────────────────
class _Check(QWidget):
    """Coche qui se dessine, ou petit arc qui tourne pendant la lecture."""
    def __init__(self):
        super().__init__()
        self.setFixedSize(30, 30)
        self.mode = "spin"       # spin | ok | warn
        self.progress = 0.0
        self._angle = 0
        self._anim = QVariantAnimation(self)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setDuration(380)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.valueChanged.connect(self._on_progress)
        self._spin = QTimer(self)
        self._spin.timeout.connect(self._tick)
        self._spin.start(30)

    def _tick(self):
        if self.mode == "spin":
            self._angle = (self._angle + 18) % 360
            self.update()

    def _on_progress(self, v):
        self.progress = float(v)
        self.update()

    def finish(self, mode):
        self.mode = mode
        self._spin.stop()
        self._anim.start()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRect(3, 3, 24, 24)
        if self.mode == "spin":
            pen = QPen(QColor(GOLD), 3); pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            p.drawArc(r, -self._angle * 16, 100 * 16)
            return
        col = QColor(GREEN if self.mode == "ok" else "#fb923c")
        p.setPen(Qt.PenStyle.NoPen)
        c = QColor(col); c.setAlpha(int(40 + 40 * self.progress))
        p.setBrush(c)
        p.drawEllipse(r)
        pen = QPen(col, 3); pen.setCapStyle(Qt.PenCapStyle.RoundCap); pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        pts = [(9, 15.5), (13.5, 20), (21, 10.5)] if self.mode == "ok" else [(15, 8.5), (15, 17)]
        lens = [((pts[i + 1][0] - pts[i][0]) ** 2 + (pts[i + 1][1] - pts[i][1]) ** 2) ** 0.5 for i in range(len(pts) - 1)]
        left = max(0.001, self.progress) * sum(lens)       # tracé progressif de la coche
        x, y = pts[0]
        for (nx, ny), ln in zip(pts[1:], lens):
            f = min(1.0, left / ln) if ln else 1.0
            p.drawLine(QPointF(x, y), QPointF(x + (nx - x) * f, y + (ny - y) * f))
            left -= ln
            x, y = nx, ny
            if left <= 0:
                break
        if self.mode == "warn" and self.progress > 0.6:
            p.drawPoint(QPointF(15, 21))


class _IconFetcher(QThread):
    done = pyqtSignal(QPixmap)
    def __init__(self, url):
        super().__init__()
        self.url = url
    def run(self):
        try:
            data = urllib.request.urlopen(urllib.request.Request(self.url, headers={"User-Agent": "DofusTeam-Organizer"}), timeout=8).read()
            pix = QPixmap()
            if pix.loadFromData(data):
                self.done.emit(pix)
        except Exception:
            pass


class Toast(QWidget):
    closed = pyqtSignal(object)

    def __init__(self):
        super().__init__(None)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
                            | Qt.WindowType.Tool | Qt.WindowType.WindowDoesNotAcceptFocus
                            | Qt.WindowType.WindowTransparentForInput)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFixedSize(340, 66)
        self._fetcher = None

        self.icon = QLabel()
        self.icon.setFixedSize(44, 44)
        self.icon.setStyleSheet(f"background:{BG3}; border-radius:10px; border:1px solid rgba(255,255,255,0.1);")
        self.icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name = QLabel("Lecture…")
        self.name.setStyleSheet(f"color:{TEXT}; font-size:13px; font-weight:700; background:transparent;")
        self.prices = QLabel("")
        self.prices.setFont(mono(9))
        self.prices.setStyleSheet(f"color:{MUT}; background:transparent;")
        self.check = _Check()

        text = QVBoxLayout(); text.setSpacing(1); text.setContentsMargins(0, 0, 0, 0)
        text.addWidget(self.name); text.addWidget(self.prices)
        lay = QHBoxLayout(self); lay.setContentsMargins(12, 11, 14, 11); lay.setSpacing(10)
        lay.addWidget(self.icon); lay.addLayout(text, 1); lay.addWidget(self.check)

        self._hide_timer = QTimer(self); self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.fade_out)
        self._anim = None
        self._edge = ACC

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QPen(QColor(255, 255, 255, 56), 1))
        p.setBrush(QColor(BG2))
        p.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 12, 12)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(self._edge))
        p.drawRoundedRect(1, 14, 3, self.height() - 28, 1.5, 1.5)

    def slide_in(self, target):
        self.move(target.x() + 24, target.y())
        self.setWindowOpacity(0.0)
        self.show()
        a = QPropertyAnimation(self, b"pos", self); a.setDuration(220)
        a.setStartValue(QPoint(target.x() + 24, target.y())); a.setEndValue(target)
        a.setEasingCurve(QEasingCurve.Type.OutCubic)
        o = QPropertyAnimation(self, b"windowOpacity", self); o.setDuration(180)
        o.setStartValue(0.0); o.setEndValue(1.0)
        a.start(); o.start()
        self._anim = (a, o)

    def move_to(self, target):
        a = QPropertyAnimation(self, b"pos", self); a.setDuration(160)
        a.setStartValue(self.pos()); a.setEndValue(target); a.setEasingCurve(QEasingCurve.Type.OutCubic)
        a.start(); self._move = a

    def set_result(self, status, name, icon_url, prices):
        ok = status == "found"
        dup = status == "duplicate"
        self._edge = GREEN if ok else (MUT if dup else "#fb923c")
        label = name or ("Objet non reconnu" if status != "error" else "Lecture impossible")
        self.name.setText(self.name.fontMetrics().elidedText(label, Qt.TextElideMode.ElideRight, 232))
        shown = [f"×{k} {int(v):,}".replace(",", " ") for k, v in sorted(((int(k), v) for k, v in (prices or {}).items()), key=lambda kv: kv[0]) if v]
        self.prices.setText("  ·  ".join(shown) if shown else ("Aucun prix lu" if status != "ambiguous" else "Plusieurs objets possibles"))
        if dup:
            self.prices.setText("Déjà pris · " + ("  ·  ".join(shown) if shown else "prix inchangés"))
        self.check.finish("ok" if (ok or dup) and shown else ("warn" if not dup else "ok"))
        if icon_url:
            self._fetcher = _IconFetcher(icon_url)
            self._fetcher.done.connect(lambda pix: self.icon.setPixmap(pix.scaled(38, 38, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)))
            self._fetcher.start()
        self.update()
        self._hide_timer.start(2600 if dup else 3600 if ok else 5200)

    def fade_out(self):
        o = QPropertyAnimation(self, b"windowOpacity", self); o.setDuration(260)
        o.setStartValue(self.windowOpacity()); o.setEndValue(0.0)
        o.finished.connect(self._done)
        o.start(); self._fade = o

    def _done(self):
        self.hide()
        self.closed.emit(self)
        self.deleteLater()



# ── Barre de commandes collée au cadre ────────────────────────────────────────
class CaptureControls(QWidget):
    start_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()
    close_clicked = pyqtSignal()

    def __init__(self):
        super().__init__(None)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
                            | Qt.WindowType.Tool | Qt.WindowType.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFixedHeight(40)
        from PyQt6.QtWidgets import QPushButton
        self.dot = QLabel("●")
        self.dot.setStyleSheet(f"color:{MUT}; background:transparent; font-size:10px;")
        self.label = QLabel("Arrêté")
        self.label.setStyleSheet(f"color:{TEXT}; background:transparent; font-size:12px; font-weight:700;")
        self.count = QLabel("")
        self.count.setFont(mono(9))
        self.count.setStyleSheet(f"color:{MUT}; background:transparent;")
        self.start_btn = QPushButton("Démarrer")
        self.stop_btn = QPushButton("Arrêter")
        for b, bg, fg in ((self.start_btn, ACC, "#080b10"), (self.stop_btn, "#1c2128", TEXT)):
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setFixedHeight(28)
            b.setStyleSheet(f"QPushButton{{background:{bg};color:{fg};border:1px solid rgba(255,255,255,0.13);border-radius:7px;padding:0 14px;font-size:12px;font-weight:700;}}"
                            f"QPushButton:hover{{border-color:rgba(255,255,255,0.3);}}")
        self.start_btn.clicked.connect(self.start_clicked.emit)
        self.stop_btn.clicked.connect(self.stop_clicked.emit)
        self.close_btn = QPushButton("✕")
        self.close_btn.setToolTip("Fermer le cadre")
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.setFixedSize(28, 28)
        self.close_btn.setStyleSheet(f"QPushButton{{background:transparent;color:{MUT};border:1px solid rgba(255,255,255,0.13);border-radius:7px;font-size:12px;padding:0;}}"
                                     f"QPushButton:hover{{color:{TEXT};background:#252d38;}}")
        self.close_btn.clicked.connect(self.close_clicked.emit)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 6, 8, 6)
        lay.setSpacing(8)
        lay.addWidget(self.dot)
        lay.addWidget(self.label)
        lay.addWidget(self.count)
        lay.addSpacing(6)
        lay.addWidget(self.start_btn)
        lay.addWidget(self.stop_btn)
        lay.addWidget(self.close_btn)
        self.set_running(False)
        self.adjustSize()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QPen(QColor(255, 255, 255, 56), 1))
        p.setBrush(QColor(BG2))
        p.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 10, 10)
        p.end()

    def set_running(self, running):
        self.start_btn.setVisible(not running)
        self.stop_btn.setVisible(running)
        self.label.setText("Capture en cours" if running else "Arrêté")
        self.dot.setStyleSheet(f"color:{GREEN if running else MUT}; background:transparent; font-size:10px;")
        self.adjustSize()

    def set_count(self, n):
        self.count.setText(f"{n} objet{'s' if n > 1 else ''}" if n else "")
        self.adjustSize()

# ── Contrôleur ────────────────────────────────────────────────────────────────
class HdvCapture(QObject):
    status_changed = pyqtSignal()

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.frame = CaptureFrame()
        self.frame.geometry_settled.connect(self._save_geometry)
        self.controls = CaptureControls()
        self.controls.start_clicked.connect(self.start_capture)
        self.controls.stop_clicked.connect(self.stop_capture)
        self.controls.close_clicked.connect(self.toggle_frame)
        self.frame.moved_or_resized.connect(self._place_controls)
        self.running = False
        self.seen = {}            # objets déjà pris pendant la session : nom → prix lus (évite de les reprendre)
        self._last_send_at = 0.0
        self.bridge = HdvBridge(config.get("hdv_origins", None))
        self.bridge.connection_changed.connect(lambda _n: self.status_changed.emit())
        self.bridge.result_received.connect(self._on_result)
        self.bridge.failed.connect(self._on_failed)
        self.toasts = []          # plus récent en dernier
        self.pending = {}         # id → Toast
        self.sent = 0
        self.read = 0
        self.last_error = ""
        self.auto = bool(config.get("hdv_auto", True))
        self._prev = None
        self._last_sent_sig = None
        self._stable = 0
        self._changed = False
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._restore_geometry()

    # ── État ──────────────────────────────────────────────────────────────────
    @property
    def frame_visible(self):
        return self.frame.isVisible()

    @property
    def connected(self):
        return self.bridge.client_count > 0

    def start(self):
        self.bridge.start()
        self._timer.start(350)

    def shutdown(self):
        self._timer.stop()
        self.bridge.stop()
        self.controls.close()
        self.frame.close()

    def set_auto(self, on):
        self.auto = bool(on)
        self.config.set("hdv_auto", self.auto)
        self.config.save()

    # ── Cadre ─────────────────────────────────────────────────────────────────
    def toggle_frame(self):
        if self.frame.isVisible():
            self.stop_capture()
            self.frame.hide()
            self.controls.hide()
        else:
            self.frame.show()
            self.controls.show()
            self._place_controls()
        self.status_changed.emit()

    def _place_controls(self):
        if not self.controls.isVisible():
            return
        r = self.frame.geometry()
        scr = (QApplication.screenAt(r.center()) or QApplication.primaryScreen()).availableGeometry()
        x = min(max(scr.left() + 4, r.x()), scr.right() - self.controls.width() - 4)
        y = r.bottom() + 6
        if y + self.controls.height() > scr.bottom():
            y = r.y() - self.controls.height() - 6
        self.controls.move(x, y)

    # ── Démarrer / arrêter ────────────────────────────────────────────────────
    def start_capture(self):
        if not self.frame.isVisible():
            self.toggle_frame()
        self.running = True
        self._prev = None
        self._stable = 0
        self._changed = False
        self.frame.set_base_state("idle")
        self.controls.set_running(True)
        self._place_controls()
        self.status_changed.emit()

    def stop_capture(self):
        self.running = False
        self.frame.set_base_state("off")
        self.controls.set_running(False)
        self._place_controls()
        self.status_changed.emit()

    def toggle_capture(self):
        if self.running:
            self.stop_capture()
        else:
            self.start_capture()

    def new_session(self):
        """Oublie les objets déjà pris : ils pourront être repris."""
        self.seen.clear()
        self.sent = 0
        self.read = 0
        self._last_sent_sig = None
        self.controls.set_count(0)
        self.status_changed.emit()

    def reset_frame(self):
        scr = QApplication.primaryScreen().availableGeometry()
        w, h = 520, 260
        self.frame.set_capture_rect(QRect(scr.center().x() - w // 2, scr.center().y() - h // 2, w, h))
        self._save_geometry()
        if not self.frame.isVisible():
            self.frame.show()
            self.controls.show()
        self._place_controls()
        self.status_changed.emit()

    def _restore_geometry(self):
        g = self.config.get("hdv_frame", None)
        if isinstance(g, list) and len(g) == 4:
            self.frame.set_capture_rect(QRect(*[int(v) for v in g]))
        else:
            scr = QApplication.primaryScreen().availableGeometry()
            self.frame.set_capture_rect(QRect(scr.center().x() - 260, scr.center().y() - 130, 520, 260))

    def _save_geometry(self):
        r = self.frame.capture_rect()
        self.config.set("hdv_frame", [r.x(), r.y(), r.width(), r.height()])
        self.config.save()

    # ── Capture ───────────────────────────────────────────────────────────────
    def _grab(self):
        r = self.frame.capture_rect()
        screen = QApplication.screenAt(r.center()) or QApplication.primaryScreen()
        sg = screen.geometry()
        pix = screen.grabWindow(0, r.x() - sg.x(), r.y() - sg.y(), r.width(), r.height())
        return pix.toImage()

    # Signature : image réduite en gris. La comparaison compte la part de pixels qui ont changé (et non l'écart moyen) :
    # quand seul le nom et les prix changent dans un cadre identique, c'est une petite zone de l'image qui bouge.
    SIG_W, SIG_H = 160, 80
    PIXEL_DELTA = 28          # écart de gris à partir duquel un pixel compte comme changé
    CHANGE_RATIO = 0.005      # part de pixels changés qui fait considérer l image comme différente (0,5 %)
    SAME_RATIO = 0.003        # en dessous, l'image est considérée comme immobile

    @classmethod
    def _signature(cls, img):
        small = img.scaled(cls.SIG_W, cls.SIG_H, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation) \
                   .convertToFormat(QImage.Format.Format_Grayscale8)
        # Grayscale8 : chaque ligne est alignée sur 4 octets, on lit pixel par pixel via bytesPerLine
        bpl = small.bytesPerLine()
        ptr = small.constBits(); ptr.setsize(small.sizeInBytes())
        raw = bytes(ptr)
        return b"".join(raw[y * bpl:y * bpl + cls.SIG_W] for y in range(cls.SIG_H))

    @classmethod
    def _ratio(cls, a, b):
        """Part (0-1) de pixels dont le gris a changé de plus de PIXEL_DELTA ; 1.0 si on ne peut pas comparer."""
        if a is None or b is None or len(a) != len(b):
            return 1.0
        d = cls.PIXEL_DELTA
        return sum(1 for x, y in zip(a, b) if abs(x - y) > d) / len(a)

    def _tick(self):
        if not (self.running and self.auto and self.frame.isVisible()):
            self._prev = None
            return
        img = self._grab()
        sig = self._signature(img)
        # image quasi uniforme (fenêtre fermée, écran noir) : rien à lire
        mean = sum(sig) / len(sig)
        if sum(abs(v - mean) for v in sig) / len(sig) < 4:
            self._prev = sig
            return
        if self._ratio(self._prev, sig) > self.CHANGE_RATIO:
            self._stable = 0
            self._changed = True
        else:
            self._stable += 1
        self._prev = sig
        # Nouvelle capture quand l'image a bougé puis s'est stabilisée (~0,7 s), qu'elle diffère de la dernière envoyée
        # (autre objet, même si le cadre est identique et que seuls le nom et les prix changent) et pas plus d'une
        # fois toutes les 0,8 s
        if self._changed and self._stable >= 2 and self._ratio(self._last_sent_sig, sig) > self.CHANGE_RATIO \
                and time.time() - self._last_send_at > 0.8:
            self._send(img, sig)

    def capture_now(self):
        if not self.frame.isVisible():
            return
        img = self._grab()
        self._send(img, self._signature(img))

    def _send(self, img, sig):
        self._changed = False
        self._last_sent_sig = sig
        self._last_send_at = time.time()
        if not self.connected:
            self.last_error = "Ouvre la page « Contribution au marché » du site pour recevoir les captures."
            self._warn_toast("Site non connecté", self.last_error)
            self.status_changed.emit()
            return
        ba = QByteArray(); buf = QBuffer(ba); buf.open(QIODevice.OpenModeFlag.WriteOnly)
        img.save(buf, "PNG")
        cid = f"{int(time.time() * 1000)}"
        if self.bridge.send_capture(cid, bytes(ba.data())):
            self.sent += 1
            self.last_error = ""
            self.frame.set_state("reading", 6000)
            self.pending[cid] = self._new_toast()
            self.status_changed.emit()

    # ── Résultats ─────────────────────────────────────────────────────────────
    def _on_result(self, msg):
        rid = str(msg.get("id"))
        t = self.pending.pop(rid, None)
        if t is None:
            # Une capture peut montrer plusieurs fiches : le site répond une fois par fiche (identifiants « <id>#2 », « <id>#3 »)
            if "#" not in rid:      # résultat inconnu ou déjà traité
                return
            t = self._new_toast()
        status = msg.get("status", "error")
        name = msg.get("name") or ""
        prices = msg.get("prices") or {}
        if status == "found":
            # Objet déjà pris pendant la session : on ne le reprend pas (le site fusionne aussi les doublons)
            if name in self.seen:
                status = "duplicate"
            else:
                self.read += 1
            self.seen[name] = prices
        elif status == "duplicate":
            self.seen[name] = prices
        self.controls.set_count(len(self.seen))
        self.frame.set_state("ok" if status == "found" else "warn" if status != "duplicate" else "idle", 1400)
        t.set_result(status, name, msg.get("icon"), prices)
        self.status_changed.emit()

    def _on_failed(self, text):
        self.last_error = text
        self.status_changed.emit()

    # ── Pile de notifications ─────────────────────────────────────────────────
    def _warn_toast(self, title, text):
        t = self._new_toast()
        t.set_result("error", title, None, {})
        t.prices.setText(text[:60])

    def _new_toast(self):
        t = Toast()
        t.closed.connect(self._toast_closed)
        self.toasts.append(t)
        if len(self.toasts) > 4:
            old = self.toasts.pop(0)
            old.fade_out()
        self._layout_toasts(first=t)
        return t

    def _toast_closed(self, t):
        if t in self.toasts:
            self.toasts.remove(t)
        self._layout_toasts()

    def _slot(self, index):
        r = self.frame.geometry()
        scr = (QApplication.screenAt(r.center()) or QApplication.primaryScreen()).availableGeometry()
        x = min(max(scr.left() + 8, r.x()), scr.right() - 340 - 8)
        above = r.y() - (index + 1) * 72 >= scr.top() + 4
        y = r.y() - (index + 1) * 72 if above else r.bottom() + 54 + index * 72
        return QPoint(x, y)

    def _layout_toasts(self, first=None):
        n = len(self.toasts)
        for i, t in enumerate(reversed(self.toasts)):   # le plus récent au plus près du cadre
            target = self._slot(i)
            if t is first:
                t.slide_in(target)
            else:
                t.move_to(target)
