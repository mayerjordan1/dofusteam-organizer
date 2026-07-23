"""
DofusTeam — calibrator.py
Overlay de calibration positionné au centre de l'écran.
Modes : 'zaap' (tous les persos), 'chat' (chef uniquement), 'all' (zaap + chat)
"""
import threading, time
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

try:
    import win32gui, win32api
    WINDOWS = True
except:
    WINDOWS = False

from paths import SKIN_DIR
from theme import BG, BG2, ACC, TEXT, MUT, GOLD, RED, make_avatar

def abs_to_rel(hwnd, ax, ay):
    try:
        r=win32gui.GetWindowRect(hwnd); w=r[2]-r[0]; h=r[3]-r[1]
        if w>0 and h>0: return (ax-r[0])/w,(ay-r[1])/h
    except: pass
    return None

class CalibOverlay(QWidget):
    _update_sig=pyqtSignal(str,str,int,int)
    _hide_sig=pyqtSignal()
    _done_sig=pyqtSignal()
    _inst_sig=pyqtSignal(str,str,str)  # title, inst, prog

    def __init__(self):
        super().__init__(None,Qt.WindowType.FramelessWindowHint|Qt.WindowType.WindowStaysOnTopHint|Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(440,100)
        self._skip_requested=False
        self._update_sig.connect(self._do_update)
        self._hide_sig.connect(self.hide)
        self._done_sig.connect(self._do_done)
        self._inst_sig.connect(self._do_inst)
        self._build()

    def _build(self):
        c=QWidget(self); c.setObjectName("c"); c.setGeometry(0,0,440,100)
        c.setStyleSheet(f"QWidget#c{{background:{BG};border:2px solid {ACC};border-radius:12px;}}")
        lay=QHBoxLayout(c); lay.setContentsMargins(14,10,14,10); lay.setSpacing(12)
        self.av=QLabel(); self.av.setFixedSize(46,46); self.av.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.addWidget(self.av)
        txt=QWidget(); tl=QVBoxLayout(txt); tl.setContentsMargins(0,0,0,0); tl.setSpacing(2)
        self.title_lbl=QLabel("Calibration"); self.title_lbl.setStyleSheet(f"font-size:13px;font-weight:700;color:{ACC};font-family:'Space Mono';")
        self.inst_lbl=QLabel(""); self.inst_lbl.setStyleSheet(f"font-size:11px;color:{TEXT};")
        self.prog_lbl=QLabel(""); self.prog_lbl.setStyleSheet(f"font-size:10px;color:{MUT};")
        tl.addWidget(self.title_lbl); tl.addWidget(self.inst_lbl); tl.addWidget(self.prog_lbl); lay.addWidget(txt); lay.addStretch()
        self.skip_btn=QPushButton("Passer"); self.skip_btn.setFixedSize(68,30)
        self.skip_btn.setStyleSheet(f"background:{BG2};color:{MUT};border:1px solid rgba(255,255,255,0.1);border-radius:6px;font-size:11px;")
        self.skip_btn.clicked.connect(self._skip); lay.addWidget(self.skip_btn)

    def _do_update(self,name,classe,cur,total):
        self.title_lbl.setText(f"Calibrer Zaap — {name}")
        self.inst_lbl.setText("Ouvre le havre-sac → clique sur le bouton Zaap")
        self.prog_lbl.setText(f"{cur}/{total} personnages")
        pix=make_avatar(classe,46)
        if pix: self.av.setPixmap(pix)
        else: self.av.setText("?"); self.av.setStyleSheet(f"color:{MUT};font-size:20px;")
        self._skip_requested=False

    def _do_inst(self,title,inst,prog):
        self.title_lbl.setText(title); self.inst_lbl.setText(inst); self.prog_lbl.setText(prog)

    def _do_done(self):
        self.title_lbl.setText("✅ Calibration terminée !")
        self.inst_lbl.setText("Toutes les positions sont sauvegardées.")
        self.prog_lbl.setText("")
        self.av.setText("✅"); self.av.setStyleSheet(f"color:{ACC};font-size:22px;")
        self.skip_btn.hide()
        QTimer.singleShot(2500,self.hide)

    def _skip(self): self._skip_requested=True

    def center_on_screen(self):
        screen=QApplication.primaryScreen().geometry()
        self.move((screen.width()-self.width())//2,(screen.height()-self.height())//2)


class CalibrationManager(QObject):
    finished=pyqtSignal()
    status=pyqtSignal(str)

    def __init__(self,config,logic,parent=None,mode='all'):
        super().__init__(parent)
        self.config=config; self.logic=logic; self.mode=mode; self._running=False
        self.overlay=CalibOverlay()

    def start(self):
        self._running=True
        threading.Thread(target=self._run,daemon=True).start()

    def stop(self):
        self._running=False

    def _run(self):
        try:
            accounts=self.logic.get_cycle_list()
            if not accounts:
                self.status.emit("⚠ Aucun compte — scannez d'abord."); self.finished.emit(); return

            if self.mode=='chat':
                self._do_chat(accounts); return

            # Zaap calibration
            total=len(accounts)
            for i,acc in enumerate(accounts):
                if not self._running: break
                name=acc["name"]; hwnd=acc["hwnd"]; classe=acc.get("classe","")
                self.logic.focus_window(hwnd); time.sleep(0.4)
                self.overlay.center_on_screen()
                self.overlay._update_sig.emit(name,classe,i+1,total)
                self.overlay.show(); self.overlay.raise_()
                self.status.emit(f"[{i+1}/{total}] Zaap de {name}...")
                clicked=self._wait_click(timeout=30)
                if clicked and not self.overlay._skip_requested:
                    rel=abs_to_rel(hwnd,clicked[0],clicked[1])
                    if rel:
                        pos=self.config.get("macro_positions",{}); pos.setdefault("zaaps",{})[name]=list(rel)
                        self.config.set("macro_positions",pos); self.config.save()
                        self.status.emit(f"✅ {name} calibré")
                self.overlay._hide_sig.emit(); time.sleep(0.3)

            # If mode=='all', also do chat
            if self._running and self.mode=='all':
                self._do_chat(accounts)
                return

            self.overlay._done_sig.emit()
            self.config.set("calibration_done",True); self.config.save()
            self.status.emit("✅ Zaap calibré pour tous les personnages !")
            self.finished.emit()
        except Exception as e:
            self.status.emit(f"❌ Erreur: {e}"); self.finished.emit()

    def _do_chat(self,accounts):
        try:
            leader_name=self.config.get("leader_name","")
            leader=next((a for a in accounts if a["name"]==leader_name),accounts[0] if accounts else None)
            if not leader:
                self.status.emit("⚠ Pas de chef défini."); self.finished.emit(); return
            hwnd=leader["hwnd"]
            self.logic.focus_window(hwnd); time.sleep(0.4)
            self.overlay.center_on_screen()
            self.overlay._update_sig.emit(leader["name"],leader.get("classe",""),1,1)
            self.overlay._inst_sig.emit(
                f"Calibration Chat — {leader['name']} (chef)",
                "Clique sur la barre de chat dans Dofus",
                "Une seule fois — sauvegardé automatiquement"
            )
            self.overlay.show(); self.overlay.raise_()
            self.status.emit("En attente du clic sur le chat...")
            clicked=self._wait_click(timeout=30)
            if clicked and not self.overlay._skip_requested:
                ax,ay=clicked
                pos=self.config.get("macro_positions",{})
                pos["chat_position"]=[ax,ay]; self.config.set("macro_positions",pos); self.config.save()
                self.status.emit(f"✅ Chat calibré à ({ax},{ay})")
            self.overlay._hide_sig.emit(); time.sleep(0.3)
            self.overlay._done_sig.emit()
            self.config.set("calibration_done",True); self.config.save()
            self.finished.emit()
        except Exception as e:
            self.status.emit(f"❌ Erreur chat: {e}"); self.finished.emit()

    def _wait_click(self,timeout=30):
        if not WINDOWS: return None
        start=time.time()
        while win32api.GetAsyncKeyState(0x01)&0x8000: time.sleep(0.02)
        time.sleep(0.15)
        while self._running and time.time()-start<timeout:
            if self.overlay._skip_requested: return None
            if win32api.GetAsyncKeyState(0x01)&0x8000:
                x,y=win32api.GetCursorPos()
                while win32api.GetAsyncKeyState(0x01)&0x8000: time.sleep(0.02)
                return x,y
            time.sleep(0.02)
        return None
