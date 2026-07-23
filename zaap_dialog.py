"""DofusTeam — zaap_dialog.py"""
import time, threading
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from paths import SKIN_DIR
from theme import STYLE, make_avatar

try:
    import pyautogui, win32gui, win32api, win32process, ctypes
    pyautogui.FAILSAFE=False
    MACRO_OK=True
except ImportError:
    MACRO_OK=False

def rel_to_abs(hwnd,rx,ry):
    rect=win32gui.GetWindowRect(hwnd)
    w=rect[2]-rect[0]; h=rect[3]-rect[1]
    return int(rect[0]+w*rx),int(rect[1]+h*ry)

def abs_to_rel(hwnd,ax,ay):
    rect=win32gui.GetWindowRect(hwnd)
    w=rect[2]-rect[0]; h=rect[3]-rect[1]
    if w<=0 or h<=0: return None
    return (ax-rect[0])/w,(ay-rect[1])/h

class ZaapDialog(QDialog):
    _status_sig=pyqtSignal(str)
    _phase2_sig=pyqtSignal()
    _done_sig=pyqtSignal()

    def __init__(self,config,logic,parent=None):
        super().__init__(parent); self.config=config; self.logic=logic
        self.executor=None; self._calib_active=False
        self.setWindowTitle("⚡ Auto-Zaap"); self.setFixedSize(520,540); self.setStyleSheet(STYLE)
        self._status_sig.connect(self._on_status)
        self._phase2_sig.connect(self._on_phase2)
        self._done_sig.connect(self._on_done)
        self._build()

    def _build(self):
        lay=QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)
        # Header + tabs
        hdr=QWidget(); hdr.setStyleSheet("background:#151922;border-bottom:1px solid rgba(255,255,255,0.06);"); hdr.setFixedHeight(50)
        hl=QHBoxLayout(hdr); hl.setContentsMargins(16,0,16,0)
        hl.addWidget(QLabel("⚡  Auto-Zaap").setStyleSheet("font-size:15px;font-weight:700;") or QLabel("⚡  Auto-Zaap")); hl.addStretch()
        self.tab_calib=QPushButton("📍 Calibration"); self.tab_exec=QPushButton("🚀 Exécution")
        for b in (self.tab_calib,self.tab_exec): b.setStyleSheet("background:transparent;border:none;color:#9ca3af;padding:5px 14px;font-size:12px;")
        self.tab_calib.clicked.connect(lambda:self._tab(0)); self.tab_exec.clicked.connect(lambda:self._tab(1))
        hl.addWidget(self.tab_calib); hl.addWidget(self.tab_exec); lay.addWidget(hdr)
        self.stack=QStackedWidget(); self.stack.addWidget(self._calib_page()); self.stack.addWidget(self._exec_page())
        lay.addWidget(self.stack); self._tab(0)

    def _tab(self,idx):
        self.stack.setCurrentIndex(idx)
        active="background:rgba(255,138,30,0.1);border-bottom:2px solid #ff8a1e;color:#ff8a1e;padding:5px 14px;font-size:12px;"
        inactive="background:transparent;border:none;color:#9ca3af;padding:5px 14px;font-size:12px;"
        self.tab_calib.setStyleSheet(active if idx==0 else inactive)
        self.tab_exec.setStyleSheet(active if idx==1 else inactive)

    def _calib_page(self):
        page=QWidget(); lay=QVBoxLayout(page); lay.setContentsMargins(16,12,16,12); lay.setSpacing(10)
        desc=QLabel("Pour chaque personnage, clique <b>Calibrer</b> puis\nclique sur le bouton Zaap dans son havre-sac Dofus."); desc.setStyleSheet("color:#9ca3af;font-size:11px;"); desc.setWordWrap(True); lay.addWidget(desc)
        dr=QHBoxLayout()
        dr.addWidget(QLabel("Délai ouverture havre-sac (s) :"))
        self.dh=QLineEdit(str(self.config.get("zaap_open_delay","0.8"))); self.dh.setFixedWidth(50); dr.addWidget(self.dh)
        dr.addSpacing(10); dr.addWidget(QLabel("Délai après clic zaap (s) :"))
        self.dz=QLineEdit(str(self.config.get("zaap_click_delay","0.5"))); self.dz.setFixedWidth(50); dr.addWidget(self.dz); dr.addStretch(); lay.addLayout(dr)
        sep=QFrame(); sep.setFrameShape(QFrame.Shape.HLine); sep.setStyleSheet("background:rgba(255,255,255,0.07);"); lay.addWidget(sep)
        scroll=QScrollArea(); scroll.setWidgetResizable(True)
        self.calib_container=QWidget(); self.calib_layout=QVBoxLayout(self.calib_container)
        self.calib_layout.setSpacing(4); self.calib_layout.setContentsMargins(0,0,0,0)
        scroll.setWidget(self.calib_container); lay.addWidget(scroll)
        self.calib_status=QLabel(""); self.calib_status.setStyleSheet("color:#ff8a1e;font-size:11px;font-weight:600;"); lay.addWidget(self.calib_status)
        self._build_calib_rows(); return page

    def _build_calib_rows(self):
        while self.calib_layout.count():
            item=self.calib_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        order=self.config.get("custom_order",[]); zaaps=self.config.get("macro_positions",{}).get("zaaps",{})
        if not order: self.calib_layout.addWidget(QLabel("Aucun compte — scannez d'abord.")); return
        for name in order:
            coords=zaaps.get(name); row=QWidget(); rl=QHBoxLayout(row); rl.setContentsMargins(4,2,4,2); rl.setSpacing(8)
            av=QLabel(); av.setFixedSize(32,32); pix=make_avatar(self.config.get("classes",{}).get(name,""))
            if pix: av.setPixmap(pix)
            rl.addWidget(av)
            lbl=QLabel(name); lbl.setMinimumWidth(110); lbl.setStyleSheet("font-weight:600;"); rl.addWidget(lbl)
            sl=QLabel(f"✅ ({coords[0]:.3f}, {coords[1]:.3f})" if coords else "❌ Non calibré")
            sl.setStyleSheet(f"color:{'#ff8a1e' if coords else '#ff5c5c'};font-size:10px;"); sl.setMinimumWidth(160); rl.addWidget(sl); rl.addStretch()
            cb=QPushButton("📍 Calibrer"); cb.setStyleSheet("background:#c8a000;color:white;border:none;border-radius:5px;padding:4px 10px;font-size:11px;")
            cb.clicked.connect(lambda _,n=name,s=sl:self._start_calib(n,s)); rl.addWidget(cb)
            self.calib_layout.addWidget(row)
        self.calib_layout.addStretch()

    def _start_calib(self,name,status_lbl):
        if self._calib_active: self.calib_status.setText("Calibration déjà en cours..."); return
        if not self.logic: self.calib_status.setText("Aucune connexion."); return
        hwnd=next((a["hwnd"] for a in self.logic.all_accounts if a["name"]==name),None)
        if hwnd: self.logic.focus_window(hwnd)
        self._calib_active=True
        self.calib_status.setText(f"🎯 Clique sur le zaap de {name} dans Dofus...")
        status_lbl.setText("⏳ En attente..."); status_lbl.setStyleSheet("color:#f4a700;font-size:10px;")
        def _wait():
            time.sleep(0.4)
            while True:
                if MACRO_OK and win32api.GetAsyncKeyState(0x01)&0x8000:
                    ax,ay=win32api.GetCursorPos()
                    self._calib_active=False
                    if hwnd:
                        rel=abs_to_rel(hwnd,ax,ay)
                        if rel:
                            pos=self.config.get("macro_positions",{})
                            pos.setdefault("zaaps",{})[name]=[rel[0],rel[1]]
                            self.config.set("macro_positions",pos); self.config.save()
                            status_lbl.setText(f"✅ ({rel[0]:.3f},{rel[1]:.3f})"); status_lbl.setStyleSheet("color:#ff8a1e;font-size:10px;")
                            self.calib_status.setText(f"✅ {name} calibré !")
                            return
                    self.calib_status.setText("❌ Erreur"); status_lbl.setText("❌ Échec"); status_lbl.setStyleSheet("color:#ff5c5c;font-size:10px;"); return
                time.sleep(0.02)
        threading.Thread(target=_wait,daemon=True).start()

    def _exec_page(self):
        page=QWidget(); lay=QVBoxLayout(page); lay.setContentsMargins(16,12,16,12); lay.setSpacing(12)
        inst=QLabel("1️⃣  <b>Phase 1</b> — L'app ouvre tous les havresacs et zaaps\n2️⃣  Sur le 1er perso : tape destination → Ctrl+A → Ctrl+C\n3️⃣  <b>Exécuter</b> — L'app colle et confirme sur tous les persos")
        inst.setStyleSheet("color:#9ca3af;font-size:11px;"); inst.setWordWrap(True); lay.addWidget(inst)
        sep=QFrame(); sep.setFrameShape(QFrame.Shape.HLine); sep.setStyleSheet("background:rgba(255,255,255,0.07);"); lay.addWidget(sep)
        self.status_box=QLabel("En attente...")
        self.status_box.setStyleSheet("background:#151922;border:1px solid rgba(255,255,255,0.07);border-radius:6px;padding:10px;font-size:12px;"); self.status_box.setWordWrap(True); self.status_box.setMinimumHeight(80); lay.addWidget(self.status_box)
        warn=QLabel("⚠️  Ne touchez pas la souris pendant l'exécution."); warn.setStyleSheet("color:#f4a700;font-size:10px;"); lay.addWidget(warn)
        lay.addStretch()
        self.p1_btn=QPushButton("▶  Lancer Phase 1 — Ouvrir les Zaaps")
        self.p1_btn.setStyleSheet("background:#ff8a1e;color:#0f1115;border:none;border-radius:6px;padding:10px;font-weight:700;font-size:13px;"); self.p1_btn.clicked.connect(self._launch_p1); lay.addWidget(self.p1_btn)
        self.exec_btn=QPushButton("⚡  Exécuter — Coller la destination")
        self.exec_btn.setStyleSheet("background:#c8a000;color:white;border:none;border-radius:6px;padding:10px;font-weight:700;font-size:13px;"); self.exec_btn.setEnabled(False); self.exec_btn.clicked.connect(self._launch_p3); lay.addWidget(self.exec_btn)
        self.stop_btn=QPushButton("■  Arrêter")
        self.stop_btn.setStyleSheet("background:#ff5c5c;color:white;border:none;border-radius:6px;padding:6px;"); self.stop_btn.setEnabled(False); self.stop_btn.clicked.connect(self._stop); lay.addWidget(self.stop_btn)
        return page

    def _launch_p1(self):
        if not self.logic or not MACRO_OK: self._on_status("Erreur: dépendances manquantes."); return
        try: self.config.set("zaap_open_delay",float(self.dh.text()))
        except: pass
        try: self.config.set("zaap_click_delay",float(self.dz.text()))
        except: pass
        self.config.save(); self.p1_btn.setEnabled(False); self.exec_btn.setEnabled(False); self.stop_btn.setEnabled(True); self._tab(1)
        from zaap_macro import ZaapExecutor
        self.executor=ZaapExecutor(self.config,self.logic,
            on_status=lambda m:self._status_sig.emit(m),
            on_phase2_ready=lambda:self._phase2_sig.emit(),
            on_done=lambda:self._done_sig.emit())
        self.executor.start()

    def _launch_p3(self):
        if self.executor: self.exec_btn.setEnabled(False); self.executor.trigger_phase3()

    def _stop(self):
        if self.executor: self.executor.stop()
        self.p1_btn.setEnabled(True); self.exec_btn.setEnabled(False); self.stop_btn.setEnabled(False); self._on_status("Arrêté.")

    def _on_status(self,msg): self.status_box.setText(msg)
    def _on_phase2(self): self.exec_btn.setEnabled(True); self.exec_btn.setStyleSheet("background:#ff8a1e;color:#0f1115;border:none;border-radius:6px;padding:10px;font-weight:700;font-size:13px;")
    def _on_done(self): self.p1_btn.setEnabled(True); self.exec_btn.setEnabled(False); self.stop_btn.setEnabled(False)
