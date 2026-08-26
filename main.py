#!/usr/bin/env python3
"""
DofusTeam — Beta V1.01
Gestionnaire multi-compte Dofus Unity
"""
import sys, json, threading, time, ctypes, random, math
from pathlib import Path
import tkinter as tk

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

try: import win32gui, win32con, win32api, win32process; WINDOWS = True
except: WINDOWS = False
try: import keyboard; KEYBOARD_OK = True
except: KEYBOARD_OK = False
try: import pyautogui, pyperclip; pyautogui.FAILSAFE = False; PYAUTOGUI_OK = True
except: PYAUTOGUI_OK = False

from paths import APP_DIR, SKIN_DIR, SOUNDS_DIR, SETTINGS_PATH
from theme import (BG, BG2, BG3, BG4, ACC, RED, GREEN, GOLD, BLUE, TEXT, MUT, BORDER,
                    STYLE, SIDEBAR_STYLE, mono, section_label, card, accent_btn, ghost_btn, make_avatar,
                    ClickableAvatar, load_icon)
from sidebar import Sidebar
from updater import UpdateCheckThread, UpdateDownloadThread, can_self_update, apply_update_and_restart

APP_NAME = "DofusTeam"
VERSION  = "V1.13"

CLASSES = ["Cra","Ecaflip","Eliotrope","Eniripsa","Enutrof","Feca","Forgelance",
           "Huppermage","Iop","Osamodas","Ouginak","Pandawa","Roublard","Sacrieur",
           "Sadida","Sram","Steamer","Xelor","Zobal"]

# ── Settings ──────────────────────────────────────────────────────────────────
DEFAULT = {
    "prev_key":"<","next_key":"tab","sync_key":"decimal",
    "toggle_app_key":"f10","refresh_key":"f5","sort_taskbar_key":"","calib_key":"f4",
    "auto_zaap_key":"","invite_group_key":"","paste_active_key":"","recall_key":"ctrl+shift+&","inventaire_key":"i","spam_click_key":"",
    "zaap_open_delay":0.8,"zaap_click_delay":0.5,"zaap_paste_delay":0.4,
    "game_haven_key":"h","game_version":"Unity","selector_key":"","zaap_favorites":[],"zaap_paste_delay":0.35,
    "leader_name":"","accounts_state":{},
    "classes":{},"custom_order":[],
    "macro_positions":{"chat_position":None,"zaaps":{}},
    "cycle_row_binds":["ctrl+F1","ctrl+F2","ctrl+F3","ctrl+F4","ctrl+F5","ctrl+F6","ctrl+F7","ctrl+F8"],
    "volume_level":50,"spam_click_interval":0.1,
    "mini_toolbar_x":100,"mini_toolbar_y":100,
    "presets":[],"team_presets":[],
    "radial_menu_active":True,"radial_menu_hotkey":"alt+left_click",
}

class Config:
    def __init__(self): self.data = dict(DEFAULT); self.load()
    def load(self):
        if SETTINGS_PATH.exists():
            try:
                with open(SETTINGS_PATH,"r",encoding="utf-8") as f: self.data.update(json.load(f))
            except: pass
    def save(self):
        try:
            with open(SETTINGS_PATH,"w",encoding="utf-8") as f: json.dump(self.data,f,indent=4,ensure_ascii=False)
        except: pass
    def get(self,k,d=None): return self.data.get(k, DEFAULT.get(k) if d is None else d)
    def set(self,k,v): self.data[k]=v

# ── Logic ─────────────────────────────────────────────────────────────────────
class DofusLogic:
    def __init__(self,config):
        self.config=config; self.all_accounts=[]; self.leader_hwnd=None; self._idx=0

    def scan_slots(self):
        if not WINDOWS: return []
        ver=self.config.get("game_version","Unity"); raw=[]
        def cb(hwnd,_):
            if not win32gui.IsWindowVisible(hwnd): return True
            t=win32gui.GetWindowText(hwnd).strip()
            if not t: return True
            c=win32gui.GetClassName(hwnd)
            if ver=="Unity":
                if c=="UnityWndClass": raw.append((hwnd,t))
            else:
                if "Dofus Retro" in t: raw.append((hwnd,t))
            return True
        win32gui.EnumWindows(cb,None)
        accounts=[]
        for hwnd,title in raw:
            if ver=="Unity":
                if title.lower().startswith("dofus"): continue
                parts=title.split(" - "); pseudo=parts[0].strip()
                if len(parts)>1:
                    cls=parts[1].strip(); c=self.config.get("classes",{}); c[pseudo]=cls; self.config.set("classes",c)
                else: cls=self.config.get("classes",{}).get(pseudo,"Inconnu")
            else:
                pseudo=title.split(" - Dofus Retro")[0].strip()
                cls=self.config.get("classes",{}).get(pseudo,"Inconnu")
            active=self.config.get("accounts_state",{}).get(pseudo,True)
            accounts.append({"name":pseudo,"hwnd":hwnd,"active":active,"classe":cls})
        order=self.config.get("custom_order",[])
        for a in accounts:
            if a["name"] not in order: order.append(a["name"])
        self.config.set("custom_order",order); self.config.save()
        # Deduplicate by name (a window can match multiple times)
        seen=set(); unique=[]
        for a in accounts:
            if a["name"] not in seen: seen.add(a["name"]); unique.append(a)
        accounts=unique
        self.all_accounts=sorted(accounts,key=lambda x:order.index(x["name"]) if x["name"] in order else 999)
        self.leader_hwnd=None
        for a in self.all_accounts:
            if a["name"]==self.config.get("leader_name",""): self.leader_hwnd=a["hwnd"]
        return self.all_accounts

    def debug_all_windows(self):
        if not WINDOWS: return []
        r=[]
        def cb(hwnd,_):
            if win32gui.IsWindowVisible(hwnd):
                t=win32gui.GetWindowText(hwnd); c=win32gui.GetClassName(hwnd)
                if t: r.append((c,t))
            return True
        win32gui.EnumWindows(cb,None); return r

    def get_cycle_list(self):
        return [a for a in self.all_accounts if a["active"]]

    def focus_window(self,hwnd):
        if not hwnd or not WINDOWS: return
        try:
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd,win32con.SW_RESTORE)
            # AttachThreadInput: proper focus steal, no Alt key = no Alt+Tab.
            # Windows n'autorise SetForegroundWindow() que si le THREAD APPELANT
            # est attaché au thread qui possède le focus courant — pas juste
            # n'importe quels deux threads. Les macros tournent dans des threads
            # Python en arrière-plan (threading.Thread), donc il faut attacher CE
            # thread-là (win32api.GetCurrentThreadId()) au thread de la fenêtre
            # au premier plan ET à celui de la fenêtre cible, sinon
            # SetForegroundWindow échoue silencieusement (reste bloqué sur la
            # même fenêtre) dès qu'on l'appelle depuis un thread de macro.
            fg = win32gui.GetForegroundWindow()
            if fg == hwnd: return  # already focused
            cur_thread = win32api.GetCurrentThreadId()
            fg_tid     = ctypes.windll.user32.GetWindowThreadProcessId(fg, None)
            target_tid = ctypes.windll.user32.GetWindowThreadProcessId(hwnd, None)
            attached_fg = attached_target = False
            if fg_tid and fg_tid != cur_thread:
                attached_fg = bool(ctypes.windll.user32.AttachThreadInput(cur_thread, fg_tid, True))
            if target_tid and target_tid != cur_thread:
                attached_target = bool(ctypes.windll.user32.AttachThreadInput(cur_thread, target_tid, True))
            try:
                ctypes.windll.user32.AllowSetForegroundWindow(0xFFFFFFFF)
                win32gui.SetForegroundWindow(hwnd)
            finally:
                if attached_fg:
                    ctypes.windll.user32.AttachThreadInput(cur_thread, fg_tid, False)
                if attached_target:
                    ctypes.windll.user32.AttachThreadInput(cur_thread, target_tid, False)
        except Exception as e:
            print(f"[focus] {e}")
            try: win32gui.BringWindowToTop(hwnd)
            except: pass

    def switch_next(self):
        lst=self.get_cycle_list()
        if not lst: return
        self._idx=(self._idx+1)%len(lst); self.focus_window(lst[self._idx]["hwnd"])
    def switch_prev(self):
        lst=self.get_cycle_list()
        if not lst: return
        self._idx=(self._idx-1)%len(lst); self.focus_window(lst[self._idx]["hwnd"])
    def switch_to_leader(self):
        if self.leader_hwnd: self.focus_window(self.leader_hwnd)
    def trigger_recall_potion(self):
        # Le raccourci renvoyé dans chaque fenêtre est le même que le déclencheur
        # global (le jeu détecte tout seul la potion, pas besoin de le distinguer)
        # → verrou pour ne pas se re-déclencher soi-même via le hook clavier
        # global pendant qu'on renvoie ce raccourci fenêtre par fenêtre.
        if getattr(self,"_recall_busy",False): return
        self._recall_busy=True
        from recall_macro import quick_recall_potion
        key=self.config.get("recall_key","")
        quick_recall_potion(self.config,self,key,on_done=lambda: setattr(self,"_recall_busy",False))
    def trigger_inventaire(self):
        # Même principe que trigger_recall_potion : le raccourci renvoyé dans
        # chaque fenêtre est le même que le déclencheur global → verrou pour
        # ne pas se re-déclencher soi-même pendant qu'on le renvoie.
        if getattr(self,"_inv_busy",False): return
        self._inv_busy=True
        from inventaire_macro import quick_inventaire
        key=self.config.get("inventaire_key","")
        quick_inventaire(self.config,self,key,on_done=lambda: setattr(self,"_inv_busy",False))
    def trigger_spam_click(self):
        if getattr(self,"_spam_busy",False): return
        self._spam_busy=True
        from spam_click_macro import quick_spam_click
        quick_spam_click(self.config,self,on_done=lambda: setattr(self,"_spam_busy",False))
    def switch_to_index(self,i):
        lst=self.get_cycle_list()
        if 0<=i<len(lst): self._idx=i; self.focus_window(lst[i]["hwnd"])
    def switch_to_name(self,name):
        for i,a in enumerate(self.get_cycle_list()):
            if a["name"]==name: self._idx=i; self.focus_window(a["hwnd"]); return

    def _sync_order(self,lst):
        order=self.config.get("custom_order",[])
        idx=[order.index(a["name"]) for a in lst if a["name"] in order]
        names=[a["name"] for a in lst if a["name"] in order]
        for i,n in zip(sorted(idx),names): order[i]=n
        self.config.set("custom_order",order); self.config.save()
        self.all_accounts.sort(key=lambda x:order.index(x["name"]) if x["name"] in order else 999)

    def move_account(self,name,d):
        active=self.get_cycle_list(); names=[a["name"] for a in active]
        if name not in names: return
        i=names.index(name); j=i+d
        if 0<=j<len(active): active[i],active[j]=active[j],active[i]; self._sync_order(active)

    def apply_preset(self,preset_order):
        """Apply a preset order to custom_order and sort taskbar."""
        current=self.config.get("custom_order",[])
        # Put preset chars first in their order, then the rest
        new_order=list(preset_order)+[n for n in current if n not in preset_order]
        self.config.set("custom_order",new_order); self.config.save()
        # Also update all_accounts order
        self.all_accounts.sort(key=lambda x:new_order.index(x["name"]) if x["name"] in new_order else 999)
        self.sort_taskbar()

    def apply_roster(self,members):
        """Active uniquement les persos du roster (les autres sortent du cycle
        Tab/fermer team/etc. sans être supprimés de la liste)."""
        members=set(members)
        state=self.config.get("accounts_state",{})
        for name in self.config.get("custom_order",[]):
            state[name]=name in members
        self.config.set("accounts_state",state); self.config.save()
        for a in self.all_accounts: a["active"]=a["name"] in members

    def set_leader(self,name):
        self.config.set("leader_name",name); self.config.save()
        self.leader_hwnd=None
        for a in self.all_accounts:
            if a["name"]==name: self.leader_hwnd=a["hwnd"]

    def refresh_all(self):
        for a in self.get_cycle_list():
            try: win32api.PostMessage(a["hwnd"],win32con.WM_KEYDOWN,win32con.VK_F5,0)
            except: pass

    def sort_taskbar(self):
        active=self.get_cycle_list()
        if not active: return
        def _s():
            for a in active: win32gui.ShowWindow(a["hwnd"],win32con.SW_HIDE)
            time.sleep(0.3)
            for a in active: win32gui.ShowWindow(a["hwnd"],win32con.SW_SHOW); time.sleep(0.1)
            if self.leader_hwnd: self.focus_window(self.leader_hwnd)
        threading.Thread(target=_s,daemon=True).start()

    def close_window(self,hwnd):
        """Ferme la fenêtre proprement (WM_CLOSE, comme un clic sur la croix) —
        laisse le client Dofus fermer sa session normalement. Un TerminateProcess
        immédiat coupait le process en plein rendu/réseau, ce qui déstabilisait
        l'appli quand l'UI redessinait juste après (plantage au clic ⏻). Si la
        fenêtre n'a pas disparu au bout de 2s, on force en dernier recours."""
        try: win32gui.PostMessage(hwnd,win32con.WM_CLOSE,0,0)
        except: pass

        def _force_if_still_open():
            try:
                if not win32gui.IsWindow(hwnd): return
                _,pid=win32process.GetWindowThreadProcessId(hwnd)
                h=ctypes.windll.kernel32.OpenProcess(1,False,pid)
                ctypes.windll.kernel32.TerminateProcess(h,0); ctypes.windll.kernel32.CloseHandle(h)
            except: pass

        t=threading.Timer(2.0,_force_if_still_open); t.daemon=True; t.start()

    def close_all(self):
        for a in self.get_cycle_list():
            self.close_window(a["hwnd"])

    def paste_active(self):
        """Colle + valide (clic position chat calibrée, Ctrl+V, Entrée x2) sur le
        chef de groupe — utilisable depuis N'IMPORTE QUELLE fenêtre (ex: un site
        web de chasse au trésor où on vient de copier des coordonnées) : bascule
        automatiquement vers le chef avant de coller, pas besoin d'être déjà sur
        une fenêtre Dofus. Sans chef défini, se rabat sur la fenêtre Dofus active.
        Double Entrée : la 1ère valide l'autocomplétion Dofus (ex: /travel), la
        2e envoie réellement le message."""
        if not WINDOWS or not PYAUTOGUI_OK: return
        cp=self.config.get("macro_positions",{}).get("chat_position")
        if not cp: return
        target_hwnd=self.leader_hwnd
        if not target_hwnd:
            try: fg=win32gui.GetForegroundWindow()
            except Exception: fg=None
            if not any(a["hwnd"]==fg for a in self.all_accounts): return
            target_hwnd=fg
        def _do():
            try:
                self.focus_window(target_hwnd); time.sleep(0.2)
                pyautogui.click(cp[0],cp[1]); time.sleep(0.15)
                pyautogui.hotkey("ctrl","v"); time.sleep(0.08)
                pyautogui.press("enter"); time.sleep(0.15)
                pyautogui.press("enter")
            except Exception as e:
                print(f"[paste_active] {e}")
        threading.Thread(target=_do,daemon=True).start()

def _typing_in_app():
    """True si DofusTeam (et pas Dofus) a le focus OS et qu'un champ de saisie
    y est actif — évite qu'une lettre tapée dans l'appli (ex: "i" dans un nom
    de roster) déclenche un raccourci global (ex: touche Inventaire)."""
    if QApplication.activeWindow() is None:
        return False
    w=QApplication.focusWidget()
    return isinstance(w,(QLineEdit,QTextEdit,QPlainTextEdit))

# ── Hotkeys ───────────────────────────────────────────────────────────────────
class HotkeyManager:
    # next_key/prev_key restent enregistrées via add_hotkey classique pour que
    # l'appui simple reste instantané (déclenché par le hook clavier, pas par un
    # polling) — un _poll_hold séparé et rapide vient juste EN PLUS pour détecter
    # le maintien de la touche et faire défiler en boucle sans devoir relâcher/
    # rappuyer à chaque changement de fenêtre (le focus steal de focus_window()
    # vers la fenêtre Dofus casse le ré-armement normal de add_hotkey en continu).
    _HOLD_INITIAL_DELAY = 0.38   # secondes avant que la répétition démarre
    _HOLD_REPEAT_INTERVAL = 0.14  # secondes entre deux répétitions
    _POLL_MS = 15

    def __init__(self,config,logic):
        self.config=config; self.logic=logic; self.active=False
        self._hold_keys={}; self._hold_state={}
        self._poll_timer=QTimer(); self._poll_timer.timeout.connect(self._poll_hold)
    def enable(self):
        if not KEYBOARD_OK or self.active: return
        self.active=True; self._reg_all(); self._poll_timer.start(self._POLL_MS)
    def disable(self):
        if not self.active: return
        self.active=False
        self._poll_timer.stop(); self._hold_state={}
        try: keyboard.unhook_all_hotkeys()
        except: pass
    def reload(self): was=self.active; self.disable(); was and self.enable()
    def _reg(self,key,fn):
        if key:
            def guarded(fn=fn):
                if _typing_in_app(): return
                fn()
            try: keyboard.add_hotkey(key,guarded,suppress=False)
            except Exception as e: print(f"[HK] {key}: {e}")
    def _reg_all(self):
        c=self.config
        def on(name): return c.get(f"{name}_on",True)
        self._hold_keys={
            "next":c.get("next_key") if on("next_key") else "",
            "prev":c.get("prev_key") if on("prev_key") else "",
        }
        self._hold_state={}
        self._reg(c.get("refresh_key") if on("refresh_key") else "",self.logic.refresh_all)
        self._reg(c.get("sort_taskbar_key"),self.logic.sort_taskbar)
        self._reg(c.get("paste_active_key") if on("paste_active_key") else "",self.logic.paste_active)
        # recall_key / inventaire_key ne sont PAS des raccourcis globaux : ce sont
        # les touches bind côté jeu, utilisées comme donnée par trigger_recall_potion/
        # trigger_inventaire pour savoir quoi renvoyer aux fenêtres Dofus. Les
        # enregistrer ici comme hotkey global faisait que taper "i" dans une
        # simple conversation privée en jeu déclenchait la macro Inventaire —
        # ces deux macros ne se lancent que via le bouton de la navbar (b_recall/b_inv).
        self._reg(c.get("spam_click_key") if on("spam_click_key") else "",self.logic.trigger_spam_click)
        # appui simple : instantané, géré par le hook clavier (pas le polling)
        self._reg(c.get("next_key") if on("next_key") else "",self.logic.switch_next)
        self._reg(c.get("prev_key") if on("prev_key") else "",self.logic.switch_prev)
        for i,b in enumerate(c.get("cycle_row_binds",[])):
            self._reg(b,lambda idx=i: self.logic.switch_to_index(idx))

    def _poll_hold(self):
        # Ne gère QUE la répétition sur maintien — le premier déclenchement est
        # déjà fait par add_hotkey ci-dessus, donc on ne tire rien ici tant que
        # le délai initial n'est pas écoulé.
        now=time.time()
        for action,key in self._hold_keys.items():
            if not key: continue
            fn=self.logic.switch_next if action=="next" else self.logic.switch_prev
            st=self._hold_state.get(key)
            try: down=keyboard.is_pressed(key)
            except Exception: down=False
            if down:
                if st is None:
                    self._hold_state[key]={"t0":now,"last":now}
                elif now-st["t0"]>=self._HOLD_INITIAL_DELAY and now-st["last"]>=self._HOLD_REPEAT_INTERVAL:
                    if not _typing_in_app(): fn()
                    st["last"]=now
            elif st is not None:
                self._hold_state.pop(key,None)

# ── Account Row ───────────────────────────────────────────────────────────────
class AccountRow(QFrame):
    sig_remove=pyqtSignal(str); sig_up=pyqtSignal(str); sig_down=pyqtSignal(str); sig_leader=pyqtSignal(str); sig_close=pyqtSignal(str)

    def __init__(self,acc,config,pos_num=0,parent=None):
        super().__init__(parent)
        self.acc=acc; self.config=config
        name=acc["name"]; live=acc.get("hwnd") is not None
        self.setFixedHeight(36)
        self.setStyleSheet("""
            AccountRow { background: transparent; border: none; border-bottom: 1px solid rgba(255,255,255,0.05); }
            AccountRow:hover { background: rgba(255,255,255,0.02); border: none; border-bottom: 1px solid rgba(255,255,255,0.05); }
        """)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 4, 8, 4)
        lay.setSpacing(8)

        # Position number — plain text
        num = QLabel(str(pos_num))
        num.setFixedWidth(16)
        num.setAlignment(Qt.AlignmentFlag.AlignCenter)
        num.setAutoFillBackground(False)
        num.setStyleSheet(f"color:{MUT};font-size:10px;font-weight:700;background:transparent;border:none;")
        lay.addWidget(num)

        # Live dot
        dot = QLabel("●" if live else "○")
        dot.setFixedWidth(10)
        dot.setAutoFillBackground(False)
        dot.setStyleSheet(f"color:{GREEN if live else '#2a3040'};font-size:9px;background:transparent;border:none;")
        lay.addWidget(dot)

        # Avatar — no border, no background — clic = bascule homme/femme
        av = ClickableAvatar()
        av.setFixedSize(28,28)
        av.setAlignment(Qt.AlignmentFlag.AlignCenter)
        av.setAutoFillBackground(False)
        av.setStyleSheet("background:transparent;border:none;")
        av.setCursor(Qt.CursorShape.PointingHandCursor)
        av.setToolTip("Clique pour changer le sexe de l'icône")
        self.av = av
        self._refresh_avatar()
        av.clicked.connect(self._toggle_sexe)
        lay.addWidget(av)

        # Name + class — une seule ligne, densifié
        name_lbl = QLabel(
            f"<span style='font-weight:600;font-size:12px;color:{TEXT};'>{name}</span>"
            f"<span style='font-size:10px;color:{MUT};'>  ·  {acc.get('classe','').upper() or 'INCONNU'}</span>"
        )
        name_lbl.setStyleSheet("background:transparent;border:none;")
        name_lbl.setMinimumWidth(100)
        lay.addWidget(name_lbl)
        lay.addStretch()

        # ── Right side buttons — plats, neutres, colorés seulement à l'état actif ──
        def icon_btn(text, tip, active=False, active_color=None, active_bg="rgba(200,160,0,0.15)", size=(26,24)):
            b = QPushButton(text); b.setFixedSize(*size); b.setToolTip(tip)
            bg = active_bg if active else "transparent"
            fg = (active_color or MUT) if active else MUT
            b.setStyleSheet(f"QPushButton{{background:{bg};color:{fg};border:none;border-radius:5px;font-size:11px;font-weight:700;}}QPushButton:hover{{background:rgba(255,255,255,0.06);}}")
            return b

        btn_up = icon_btn("▲", "Monter")
        btn_up.clicked.connect(lambda: self.sig_up.emit(name)); lay.addWidget(btn_up)
        btn_dn = icon_btn("▼", "Descendre")
        btn_dn.clicked.connect(lambda: self.sig_down.emit(name)); lay.addWidget(btn_dn)

        # Star — accent quand chef
        is_leader = config.get("leader_name") == name
        self.star = icon_btn("★", "Définir comme chef", active=is_leader, active_color=GOLD)
        self.star.clicked.connect(lambda: self.sig_leader.emit(name)); lay.addWidget(self.star)

        # Close window — ferme juste la fenêtre Dofus de ce compte (process kill),
        # sans le retirer de la liste — plus rapide qu'un clic droit > Fermer.
        close = QPushButton("⏻")
        close.setFixedSize(26,24)
        close.setEnabled(live)
        close.setToolTip("Fermer cette fenêtre Dofus" if live else "Aucune fenêtre détectée pour ce compte")
        close.setStyleSheet(
            f"QPushButton{{background:transparent;color:{RED if live else '#3a4050'};border:none;border-radius:5px;font-size:12px;font-weight:700;}}"
            f"QPushButton:hover{{background:rgba(224,85,85,0.14);}}"
            f"QPushButton:disabled{{background:transparent;}}"
        )
        close.clicked.connect(lambda: self.sig_close.emit(name)); lay.addWidget(close)

        # Remove
        rm = icon_btn("✕", "Retirer de la liste", size=(26,24))
        rm.clicked.connect(lambda: self.sig_remove.emit(name)); lay.addWidget(rm)

    def _refresh_avatar(self):
        name = self.acc["name"]
        sexe = self.config.get("sexes",{}).get(name,"h")
        pix = make_avatar(self.acc.get("classe",""), 26, sexe)
        if pix: self.av.setPixmap(pix)
        else: self.av.setText("?"); self.av.setStyleSheet(f"color:{MUT};font-size:13px;background:transparent;")

    def _toggle_sexe(self):
        name = self.acc["name"]
        sexes = self.config.get("sexes",{})
        sexes[name] = "f" if sexes.get(name,"h")=="h" else "h"
        self.config.set("sexes",sexes); self.config.save()
        self._refresh_avatar()

# ── Preset Panel ──────────────────────────────────────────────────────────────
class PresetPanel(QWidget):
    preset_applied = pyqtSignal()

    def __init__(self,config,logic,parent=None):
        super().__init__(parent); self.config=config; self.logic=logic
        lay=QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(8)
        hrow=QHBoxLayout()
        hrow.addWidget(section_label("PRESETS D'INITIATIVE")); hrow.addStretch()
        add=QPushButton("+"); add.setFixedSize(24,24)
        add.setStyleSheet(f"background:rgba(255,138,30,0.12);color:{ACC};border:1px solid rgba(255,138,30,0.3);border-radius:5px;font-size:14px;font-weight:700;")
        add.setToolTip("Nouveau preset"); add.clicked.connect(self._new_preset); hrow.addWidget(add)
        lay.addLayout(hrow)
        self.scroll=QScrollArea(); self.scroll.setWidgetResizable(True); self.scroll.setMaximumHeight(160)
        self.container=QWidget(); self.vlay=QVBoxLayout(self.container)
        self.vlay.setContentsMargins(0,0,0,0); self.vlay.setSpacing(4); self.vlay.addStretch()
        self.scroll.setWidget(self.container); lay.addWidget(self.scroll)
        self.refresh_presets()

    def refresh_presets(self):
        while self.vlay.count()>1:
            item=self.vlay.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        presets=self.config.get("presets",[])
        if not presets:
            empty=QLabel("Aucun preset — crée-en un avec +")
            empty.setStyleSheet(f"color:{MUT};font-size:11px;"); self.vlay.insertWidget(0,empty); return
        classes=self.config.get("classes",{})
        for i,p in enumerate(presets):
            row=QWidget(); rl=QHBoxLayout(row); rl.setContentsMargins(8,4,8,4); rl.setSpacing(8)
            row.setObjectName(f"PresetRow{i}")
            row.setStyleSheet(f"QWidget#PresetRow{i}{{background:{BG2};border-radius:6px;}}")
            p_order=p.get("order",[])
            if p_order:
                icon_av=QLabel(); icon_av.setFixedSize(20,20)
                icon_av.setStyleSheet("background:transparent;")
                icon_pix=make_avatar(classes.get(p_order[0],""),20)
                if icon_pix: icon_av.setPixmap(icon_pix)
                rl.addWidget(icon_av)
            name_lbl=QLabel(p["name"]); name_lbl.setStyleSheet(f"font-weight:700;font-size:12px;color:{TEXT};"); rl.addWidget(name_lbl)
            count=QLabel(f"{len(p.get('order',[]))} persos"); count.setStyleSheet(f"color:{MUT};font-size:10px;"); rl.addWidget(count)
            rl.addStretch()
            apply=QPushButton("▶ Appliquer")
            apply.setStyleSheet(f"background:rgba(255,138,30,0.1);color:{ACC};border:1px solid rgba(255,138,30,0.25);border-radius:5px;padding:3px 10px;font-size:11px;font-weight:700;")
            apply.clicked.connect(lambda _,p=p: self._apply(p)); rl.addWidget(apply)
            edit=QPushButton("✏"); edit.setFixedSize(24,24)
            edit.setStyleSheet(f"background:rgba(255,255,255,0.04);color:{MUT};border:none;border-radius:4px;"); edit.clicked.connect(lambda _,idx=i: self._edit_preset(idx)); rl.addWidget(edit)
            rm=QPushButton("✕"); rm.setFixedSize(24,24)
            rm.setStyleSheet(f"QPushButton{{background:transparent;color:rgba(224,85,85,0.35);border:none;border-radius:4px;}}QPushButton:hover{{color:{RED};background:rgba(224,85,85,0.1);}}")
            rm.clicked.connect(lambda _,idx=i: self._delete(idx)); rl.addWidget(rm)
            self.vlay.insertWidget(self.vlay.count()-1,row)

    def _apply(self,preset):
        self.logic.apply_preset(preset.get("order",[]))
        self.preset_applied.emit()

    def _delete(self,idx):
        presets=self.config.get("presets",[]); presets.pop(idx)
        self.config.set("presets",presets); self.config.save(); self.refresh_presets()

    def _new_preset(self): self._open_editor(-1)
    def _edit_preset(self,idx): self._open_editor(idx)

    def _open_editor(self,idx):
        dlg=PresetEditor(self.config,idx,self); dlg.saved.connect(self.refresh_presets); dlg.exec()

class PresetEditor(QDialog):
    saved=pyqtSignal()
    def __init__(self,config,idx,parent=None,initial_order=None):
        super().__init__(parent); self.config=config; self.idx=idx
        presets=self.config.get("presets",[])
        if idx>=0 and idx<len(presets):
            self.preset=presets[idx].copy()
        else:
            self.preset={"name":"","order":list(initial_order) if initial_order else []}
        self.setWindowTitle("Preset d'initiative"); self.setFixedSize(360,480); self.setStyleSheet(STYLE)
        self._build()

    def _build(self):
        lay=QVBoxLayout(self); lay.setContentsMargins(16,16,16,16); lay.setSpacing(12)
        lay.addWidget(QLabel("Nom du preset :"))
        self.name_inp=QLineEdit(self.preset.get("name","")); self.name_inp.setPlaceholderText("Ex: Farm Abysse"); lay.addWidget(self.name_inp)
        lay.addWidget(QLabel("Ordre des personnages (glisser-déposer pour réordonner) :"))

        # Liste des personnages connus, avec cases à cocher + drag & drop pour réordonner
        self.list=QListWidget()
        self.list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.list.setStyleSheet(f"QListWidget{{background:{BG3};border:none;border-radius:6px;}}QListWidget::item{{border:none;}}")
        lay.addWidget(self.list)
        self._build_char_list()

        btns=QHBoxLayout()
        cancel=ghost_btn("Annuler",self.reject); btns.addWidget(cancel)
        save=accent_btn("💾 Sauvegarder",self._save); btns.addWidget(save)
        lay.addLayout(btns)

    def _build_char_list(self):
        self.list.clear()
        all_known=self.config.get("custom_order",[])
        preset_order=self.preset.get("order",[])
        # Show preset order first, then unselected
        ordered=[n for n in preset_order if n in all_known]+[n for n in all_known if n not in preset_order]
        self.checks={}
        for name in ordered:
            row=QWidget(); rl=QHBoxLayout(row); rl.setContentsMargins(8,6,8,6); rl.setSpacing(10)
            chk=QCheckBox(); chk.setChecked(name in preset_order); rl.addWidget(chk)
            av=QLabel(); av.setFixedSize(28,28)
            av.setStyleSheet("background:transparent;border:none;")
            pix=make_avatar(self.config.get("classes",{}).get(name,""),28)
            if pix: av.setPixmap(pix)
            rl.addWidget(av)
            lbl=QLabel(name); lbl.setStyleSheet(f"font-weight:600;color:{TEXT};background:transparent;border:none;"); rl.addWidget(lbl)
            rl.addStretch()
            self.checks[name]=chk
            item=QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole,name)
            # row.sizeHint() sous-estime la hauteur tant que le widget n'a pas
            # encore été layouté dans la liste — on force une hauteur minimale
            # explicite pour éviter que l'avatar/checkbox soient écrasés.
            hint=row.sizeHint()
            item.setSizeHint(QSize(hint.width(),max(hint.height(),40)))
            self.list.addItem(item)
            self.list.setItemWidget(item,row)

    def _save(self):
        name=self.name_inp.text().strip()
        if not name: return
        order=[]
        for i in range(self.list.count()):
            item=self.list.item(i)
            n=item.data(Qt.ItemDataRole.UserRole)
            if self.checks[n].isChecked():
                order.append(n)
        preset={"name":name,"order":order}
        presets=self.config.get("presets",[])
        if self.idx>=0 and self.idx<len(presets): presets[self.idx]=preset
        else: presets.append(preset)
        self.config.set("presets",presets); self.config.save()
        self.saved.emit(); self.accept()

class RosterPanel(QWidget):
    """Presets de roster : chaque roster est une liste indépendante de persos
    (un même perso peut appartenir à plusieurs rosters). Appliquer un roster
    active ces persos-là et désactive les autres dans le cycle Tab/fermer
    team/etc. via DofusLogic.apply_roster() — ne touche pas à l'ordre."""
    roster_applied = pyqtSignal()

    def __init__(self,config,logic,parent=None):
        super().__init__(parent); self.config=config; self.logic=logic
        lay=QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(8)
        hrow=QHBoxLayout()
        hrow.addWidget(section_label("ROSTERS")); hrow.addStretch()
        add=QPushButton("+"); add.setFixedSize(24,24)
        add.setStyleSheet(f"background:rgba(255,138,30,0.12);color:{ACC};border:1px solid rgba(255,138,30,0.3);border-radius:5px;font-size:14px;font-weight:700;")
        add.setToolTip("Nouveau roster"); add.clicked.connect(self._new_roster); hrow.addWidget(add)
        lay.addLayout(hrow)
        self.container=QWidget(); self.vlay=QVBoxLayout(self.container)
        self.vlay.setContentsMargins(0,0,0,0); self.vlay.setSpacing(4); self.vlay.addStretch()
        lay.addWidget(self.container)
        self.refresh_rosters()

    def refresh_rosters(self):
        while self.vlay.count()>1:
            item=self.vlay.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        rosters=self.config.get("team_presets",[])
        if not rosters:
            empty=QLabel("Aucun roster — crée-en un avec +")
            empty.setStyleSheet(f"color:{MUT};font-size:11px;"); self.vlay.insertWidget(0,empty); return
        classes=self.config.get("classes",{})
        for i,r in enumerate(rosters):
            row=QWidget(); rl=QHBoxLayout(row); rl.setContentsMargins(8,4,8,4); rl.setSpacing(8)
            row.setObjectName(f"RosterRow{i}")
            row.setStyleSheet(f"QWidget#RosterRow{i}{{background:{BG2};border-radius:6px;}}")
            members=r.get("members",[])
            if members:
                icon_av=QLabel(); icon_av.setFixedSize(20,20)
                icon_av.setStyleSheet("background:transparent;")
                icon_pix=make_avatar(classes.get(members[0],""),20)
                if icon_pix: icon_av.setPixmap(icon_pix)
                rl.addWidget(icon_av)
            name_lbl=QLabel(r["name"]); name_lbl.setStyleSheet(f"font-weight:700;font-size:12px;color:{TEXT};"); rl.addWidget(name_lbl)
            count=QLabel(f"{len(members)} persos"); count.setStyleSheet(f"color:{MUT};font-size:10px;"); rl.addWidget(count)
            rl.addStretch()
            apply=QPushButton("▶ Appliquer")
            apply.setStyleSheet(f"background:rgba(255,138,30,0.1);color:{ACC};border:1px solid rgba(255,138,30,0.25);border-radius:5px;padding:3px 10px;font-size:11px;font-weight:700;")
            apply.clicked.connect(lambda _,r=r: self._apply(r)); rl.addWidget(apply)
            edit=QPushButton("✏"); edit.setFixedSize(24,24)
            edit.setStyleSheet(f"background:rgba(255,255,255,0.04);color:{MUT};border:none;border-radius:4px;"); edit.clicked.connect(lambda _,idx=i: self._edit_roster(idx)); rl.addWidget(edit)
            rm=QPushButton("✕"); rm.setFixedSize(24,24)
            rm.setStyleSheet(f"QPushButton{{background:transparent;color:rgba(224,85,85,0.35);border:none;border-radius:4px;}}QPushButton:hover{{color:{RED};background:rgba(224,85,85,0.1);}}")
            rm.clicked.connect(lambda _,idx=i: self._delete(idx)); rl.addWidget(rm)
            self.vlay.insertWidget(self.vlay.count()-1,row)

    def _apply(self,roster):
        self.logic.apply_roster(roster.get("members",[]))
        self.roster_applied.emit()

    def _delete(self,idx):
        rosters=self.config.get("team_presets",[]); rosters.pop(idx)
        self.config.set("team_presets",rosters); self.config.save(); self.refresh_rosters()

    def _new_roster(self): self._open_editor(-1)
    def _edit_roster(self,idx): self._open_editor(idx)

    def _open_editor(self,idx):
        dlg=RosterEditor(self.config,idx,self); dlg.saved.connect(self.refresh_rosters); dlg.exec()

class RosterEditor(QDialog):
    saved=pyqtSignal()
    def __init__(self,config,idx,parent=None):
        super().__init__(parent); self.config=config; self.idx=idx
        rosters=self.config.get("team_presets",[])
        if idx>=0 and idx<len(rosters):
            self.roster=rosters[idx].copy()
        else:
            self.roster={"name":"","members":[]}
        self.setWindowTitle("Roster d'équipe"); self.setFixedSize(360,480); self.setStyleSheet(STYLE)
        self._build()

    def _build(self):
        lay=QVBoxLayout(self); lay.setContentsMargins(16,16,16,16); lay.setSpacing(12)
        lay.addWidget(QLabel("Nom du roster :"))
        self.name_inp=QLineEdit(self.roster.get("name","")); self.name_inp.setPlaceholderText("Ex: Farm Abysse"); lay.addWidget(self.name_inp)
        lay.addWidget(QLabel("Personnages du roster :"))

        scroll=QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"QScrollArea{{background:{BG3};border:none;border-radius:6px;}}")
        list_w=QWidget(); list_l=QVBoxLayout(list_w); list_l.setContentsMargins(6,6,6,6); list_l.setSpacing(2)
        scroll.setWidget(list_w); lay.addWidget(scroll)
        self._build_char_list(list_l)

        btns=QHBoxLayout()
        cancel=ghost_btn("Annuler",self.reject); btns.addWidget(cancel)
        save=accent_btn("💾 Sauvegarder",self._save); btns.addWidget(save)
        lay.addLayout(btns)

    def _build_char_list(self,list_l):
        all_known=self.config.get("custom_order",[])
        members=self.roster.get("members",[])
        self.checks={}
        for name in all_known:
            row=QWidget(); rl=QHBoxLayout(row); rl.setContentsMargins(8,6,8,6); rl.setSpacing(10)
            chk=QCheckBox(); chk.setChecked(name in members); rl.addWidget(chk)
            av=QLabel(); av.setFixedSize(28,28)
            av.setStyleSheet("background:transparent;border:none;")
            pix=make_avatar(self.config.get("classes",{}).get(name,""),28)
            if pix: av.setPixmap(pix)
            rl.addWidget(av)
            lbl=QLabel(name); lbl.setStyleSheet(f"font-weight:600;color:{TEXT};background:transparent;border:none;"); rl.addWidget(lbl)
            rl.addStretch()
            self.checks[name]=chk
            list_l.addWidget(row)
        list_l.addStretch()

    def _save(self):
        name=self.name_inp.text().strip()
        if not name: return
        members=[n for n,chk in self.checks.items() if chk.isChecked()]
        roster={"name":name,"members":members}
        rosters=self.config.get("team_presets",[])
        if self.idx>=0 and self.idx<len(rosters): rosters[self.idx]=roster
        else: rosters.append(roster)
        self.config.set("team_presets",rosters); self.config.save()
        self.saved.emit(); self.accept()

# ── Mini Toolbar ──────────────────────────────────────────────────────────────
class MiniToolbar(QWidget):
    """Barre flottante — inspirée du style overlay de DoFrame (capture fournie par
    l'utilisateur) : poignée + logo + libellé de mode à gauche, bande d'avatars des
    personnages détectés au centre (pastille de statut), actions rapides à droite
    (chef/havre-sac/zaap/plus), puis réduire/fermer. « Réduire » replie la barre en
    une petite pastille (self.nub) — même geste que le second aperçu de la capture."""

    def __init__(self,config,logic,on_show,on_navigate=None):
        super().__init__(None,Qt.WindowType.Tool|Qt.WindowType.FramelessWindowHint|Qt.WindowType.WindowStaysOnTopHint)
        self.config=config; self.logic=logic; self.on_show=on_show; self.on_navigate=on_navigate; self._drag=None
        self._collapsed=False
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        def mkb(icon,tip,color=BG3,ck=False,icon_file=None,icon_pixmap=None,size=(32,30),icon_size=18):
            b=QPushButton("" if (icon_file or icon_pixmap) else icon); b.setFixedSize(*size); b.setToolTip(tip); b.setCheckable(ck)
            b.setStyleSheet(f"QPushButton{{background:{color};color:white;border:none;border-radius:6px;font-size:14px;}}QPushButton:checked{{background:{ACC};color:#0f1115;}}")
            if icon_file:
                ic=load_icon(icon_file,icon_size)
                if ic: b.setIcon(ic); b.setIconSize(QSize(icon_size,icon_size))
                else: b.setText(icon)  # PNG absent du skin/ → fallback emoji
            elif icon_pixmap is not None:
                b.setIcon(QIcon(icon_pixmap)); b.setIconSize(icon_pixmap.size())
            return b
        def sep():
            s=QFrame(); s.setFrameShape(QFrame.Shape.VLine)
            s.setStyleSheet("color:rgba(255,255,255,0.1);"); s.setFixedHeight(24); s.setFixedWidth(1)
            return s

        # ── Barre complète ──────────────────────────────────────────────
        bar=QWidget(self); bar.setObjectName("b")
        bar.setStyleSheet(f"QWidget#b{{background:{BG};border:1px solid rgba(255,138,30,0.35);border-radius:12px;}}")
        lay=QHBoxLayout(bar); lay.setContentsMargins(10,6,8,6); lay.setSpacing(6)
        self.bar=bar; self._inner_lay=lay

        grip=QLabel("⋮⋮"); grip.setFixedWidth(10)
        grip.setStyleSheet(f"color:{MUT};font-size:11px;letter-spacing:-2px;background:transparent;")
        lay.addWidget(grip)

        egg=load_icon("logo.png",18)
        logo=QPushButton()
        logo.setFixedSize(24,24)
        logo.setCursor(Qt.CursorShape.PointingHandCursor)
        logo.setToolTip("Réafficher la fenêtre principale de DofusTeam")
        if egg: logo.setIcon(egg); logo.setIconSize(QSize(18,18))
        logo.setStyleSheet("QPushButton{background:transparent;border:none;}QPushButton:hover{background:rgba(255,255,255,0.08);border-radius:5px;}")
        logo.clicked.connect(lambda: self.on_show())
        lay.addWidget(logo)

        # Bande d'avatars — peuplée par _rebuild_char_icons(), séparateur affiché
        # seulement quand des comptes sont détectés (garde l'aspect « replié » avant scan).
        self._char_sep=sep(); self._char_sep.setVisible(False)
        lay.addWidget(self._char_sep)
        self._char_container=QWidget()
        self._char_lay=QHBoxLayout(self._char_container)
        self._char_lay.setContentsMargins(0,0,0,0); self._char_lay.setSpacing(6)
        lay.addWidget(self._char_container)
        self._char_btns=[]

        lay.addWidget(sep())

        self.b_hsac=mkb("🏠","Havre-sac + Zaap\n1. Appuie H sur tous les persos\n2. Clique zaap calibré sur tous",BG,icon_file="havre-sac.png",size=(40,30),icon_size=28)
        self.b_zaap=mkb("⚡","Zaap favoris ⭐\nOuvre havre-sac + zaap puis colle/valide directement la destination favorite sur tous les persos",BG,icon_file="icon_zaap.png",size=(40,30),icon_size=28)
        self.b_recall=mkb("🧪","Potion de rappel\nSwitch de fenêtre + renvoie le raccourci de rappel sur tous les persos (déjà bind côté jeu)",BG,icon_file="potion-rappel.png",size=(40,30),icon_size=28)
        self.b_inv=mkb("🎒","Inventaire\nSwitch de fenêtre + renvoie le raccourci inventaire sur tous les persos (déjà bind côté jeu)",BG,icon_file="inventaire.png",size=(40,30),icon_size=28)
        self.b_hsac.clicked.connect(self._quick_hsac)
        self.b_hsac.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.b_hsac.customContextMenuRequested.connect(lambda: self._show_zaap_menu())
        self.b_hsac.setToolTip("🏠 Havre-sac + Zaap\nClic gauche: ouvrir tous les havresacs\nClic droit: zaap favoris ⭐")
        self.b_zaap.clicked.connect(self._quick_zaap)
        self.b_recall.clicked.connect(lambda: self.logic.trigger_recall_potion() if self.logic else None)
        self.b_inv.clicked.connect(lambda: self.logic.trigger_inventaire() if self.logic else None)
        for w in (self.b_hsac,self.b_zaap,self.b_recall,self.b_inv): lay.addWidget(w)

        lay.addWidget(sep())

        self.b_min=mkb("–","Réduire",size=(26,30))
        self.b_close=mkb("✕","Fermer la barre (revenir à DofusTeam)",size=(26,30))
        self.b_min.clicked.connect(self._toggle_collapse)
        self.b_close.clicked.connect(lambda:(self.hide(),self.on_show()))
        lay.addWidget(self.b_min); lay.addWidget(self.b_close)

        bar.adjustSize(); bar.move(0,0)

        # ── Pastille repliée (état « minimisé ») ────────────────────────
        nub=QWidget(self); nub.setObjectName("n")
        nub.setStyleSheet(f"QWidget#n{{background:{BG};border:1px solid rgba(255,138,30,0.35);border-radius:18px;}}")
        nlay=QHBoxLayout(nub); nlay.setContentsMargins(6,4,6,4); nlay.setSpacing(4)
        nub_logo=QLabel()
        if egg: nub_logo.setPixmap(egg.pixmap(18,18))
        nub_logo.setStyleSheet("background:transparent;")
        nlay.addWidget(nub_logo)
        expand=QPushButton("»"); expand.setFixedSize(20,20)
        expand.setStyleSheet(f"QPushButton{{background:transparent;color:{MUT};border:none;font-size:13px;font-weight:700;}}QPushButton:hover{{color:{ACC};}}")
        expand.clicked.connect(self._toggle_collapse)
        nlay.addWidget(expand)
        nub.adjustSize(); nub.hide()
        self.nub=nub

        self.resize(bar.sizeHint().width(),bar.sizeHint().height())
        self.move(config.get("mini_toolbar_x",100),config.get("mini_toolbar_y",100))

    def _toggle_collapse(self):
        self._collapsed = not self._collapsed
        self.bar.setVisible(not self._collapsed)
        self.nub.setVisible(self._collapsed)
        target = self.nub if self._collapsed else self.bar
        self.resize(target.sizeHint().width(), target.sizeHint().height())

    def update_focus(self,name): self.focus_lbl.setText(name[:10] if name else "—")
    def _quick_zaap(self):
        """Clic sur ⚡ Zaap → liste des favoris (menu identique à l'ancien clic
        droit sur 🏠) : sélectionner un favori ouvre tout + colle/valide la
        destination directement, sans étape manuelle de copier-coller."""
        self._show_zaap_menu()

    def _quick_hsac(self):
        if not PYAUTOGUI_OK or not self.logic: return
        from zaap_macro import quick_havresac_zaap
        quick_havresac_zaap(self.config, self.logic, on_status=lambda m:print(f"[hsac]{m}"))

    def _show_zaap_menu(self):
        """Right-click on zaap button → favorites menu."""
        from zaap_data import ZAAPS, get_favorites
        from zaap_favorites import run_zaap_to_destination
        favs = get_favorites(self.config)
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu{{background:#151922;color:#f3f4f6;border:1px solid rgba(255,138,30,0.3);border-radius:8px;padding:4px;}}
            QMenu::item{{padding:7px 20px;border-radius:5px;font-size:12px;}}
            QMenu::item:selected{{background:#1b2130;color:#ff8a1e;}}
            QMenu::separator{{background:rgba(255,255,255,0.07);height:1px;margin:4px 8px;}}
        """)
        menu.addAction("⭐  Gérer les favoris").triggered.connect(self._open_fav_manager)
        if favs:
            menu.addSeparator()
            for name in favs:
                menu.addAction(f"⚡  {name}").triggered.connect(
                    lambda _, n=name: run_zaap_to_destination(self.config, self.logic, n,
                        on_status=lambda m: print(f"[zaap_fav]{m}"))
                )
        menu.exec(self.b_hsac.mapToGlobal(self.b_hsac.rect().bottomLeft()))

    def _open_fav_manager(self):
        if self.on_navigate:
            self.on_show()
            self.on_navigate("zaap_menu")
            return
        from zaap_favorites import ZaapFavoritesDialog
        ZaapFavoritesDialog(self.config, self).exec()

    def _rebuild_char_icons(self, accounts):
        """Rebuild character icon strip after scan — avatars ronds + pastille de statut
        (style bande d'avatars DoFrame), peuplés dans self._char_lay (voir __init__)."""
        while self._char_lay.count():
            item = self._char_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._char_btns = []
        # Défensif : un même hwnd ne doit apparaître qu'une fois (évite un
        # doublon si un scan renvoie deux fois la même fenêtre).
        seen_hwnds = set()
        deduped = []
        for acc in accounts:
            h = acc.get("hwnd")
            if h is not None and h in seen_hwnds:
                continue
            if h is not None:
                seen_hwnds.add(h)
            deduped.append(acc)
        accounts = deduped
        self._char_sep.setVisible(bool(accounts))

        for acc in accounts:
            stack = QWidget(); stack.setFixedSize(32, 32)
            b = QPushButton(stack); b.setGeometry(0, 0, 32, 32); b.setToolTip(acc["name"])
            pix = make_avatar(acc.get("classe", ""), 28)
            if pix: b.setIcon(QIcon(pix)); b.setIconSize(QSize(28, 28))
            b.setStyleSheet(
                f"QPushButton{{background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.08);border-radius:16px;}}"
                f"QPushButton:hover{{background:rgba(255,138,30,0.15);border-color:#ff8a1e;}}"
            )
            b.clicked.connect(lambda _, n=acc["name"]: self.logic.switch_to_name(n) if self.logic else None)
            dot = QLabel(stack); dot.setGeometry(22, 22, 9, 9)
            dot.setStyleSheet(f"background:{GREEN}; border-radius:4px; border:2px solid {BG};")
            self._char_lay.addWidget(stack)
            self._char_btns.append(b)

        # La fenêtre a une taille fixe posée au __init__ — sans ce ré-ajustement,
        # les icônes de personnages ajoutées ci-dessus sont coupées par le bord de la fenêtre.
        # Le conteneur d'avatars a sa propre layout imbriquée : il faut l'activer avant
        # celle de la barre, sinon adjustSize() lit un sizeHint pas encore recalculé.
        self._char_lay.activate()
        self._char_container.adjustSize()
        self.bar.layout().activate()
        self.bar.adjustSize()
        self.resize(self.bar.width(), self.bar.height())

        if not hasattr(self, '_focus_timer'):
            self._focus_timer = QTimer(); self._focus_timer.timeout.connect(self._update_focus_highlight)
            self._focus_timer.start(500)

    def _update_focus_highlight(self):
        if not WINDOWS or not hasattr(self, '_char_btns'): return
        try: fg = win32gui.GetForegroundWindow()
        except: return
        accounts = self.logic.get_cycle_list() if self.logic else []
        hwnd_map = {a["hwnd"]: a["name"] for a in accounts if a.get("hwnd")}
        fg_name = hwnd_map.get(fg)
        for i, b in enumerate(self._char_btns):
            if i < len(accounts):
                is_active = (accounts[i]["name"] == fg_name)
                b.setStyleSheet(
                    f"QPushButton{{background:{'rgba(255,138,30,0.2)' if is_active else 'rgba(255,255,255,0.05)'};border:{'2px solid #ff8a1e' if is_active else '1px solid rgba(255,255,255,0.08)'};border-radius:16px;}}"
                    f"QPushButton:hover{{background:rgba(255,138,30,0.15);border-color:#ff8a1e;}}"
                )

    def mousePressEvent(self,e):
        if e.button()==Qt.MouseButton.LeftButton: self._drag=e.globalPosition().toPoint()-self.frameGeometry().topLeft()
    def mouseMoveEvent(self,e):
        if self._drag and e.buttons()==Qt.MouseButton.LeftButton: self.move(e.globalPosition().toPoint()-self._drag)
    def mouseReleaseEvent(self,e):
        if self._drag:
            self.config.set("mini_toolbar_x",self.x()); self.config.set("mini_toolbar_y",self.y()); self.config.save(); self._drag=None

# ── Scan Thread ───────────────────────────────────────────────────────────────
class ScanThread(QThread):
    done=pyqtSignal(list)
    def __init__(self,logic): super().__init__(); self.logic=logic
    def run(self): self.done.emit(self.logic.scan_slots())

# ── Main Window ───────────────────────────────────────────────────────────────
class _BackgroundWidget(QWidget):
    """Widget racine peignant le fond décoratif DofusTeam : une base statique
    mise en cache (vignette + étoiles, skin/bg_app_base.jpg) + 3 halos orange
    qui dérivent très lentement en direct — version allégée du fond animé du
    site (BackgroundFX.tsx). Repaint à ~7 fps seulement (le mouvement est lent,
    58-84s par boucle) et coupé quand la fenêtre est cachée, pour ne pas peser
    sur le CPU pendant que Dofus tourne en multi-compte à côté."""

    FLOWS = [
        dict(sx=-0.35, sy=0.22, ex=1.35, ey=0.60, speed=1/58000, r=0.40, alpha=0.055, elong=2.8),
        dict(sx=1.35, sy=0.72, ex=-0.25, ey=0.28, speed=1/72000, r=0.34, alpha=0.042, elong=2.5),
        dict(sx=0.05, sy=1.18, ex=0.88, ey=-0.08, speed=1/84000, r=0.30, alpha=0.038, elong=2.2),
    ]

    def __init__(self,parent=None):
        super().__init__(parent)
        p=SKIN_DIR/"bg_app_base.jpg"
        self._base=QPixmap(str(p)) if p.exists() else None
        self._scaled_base=None
        self._clock=QElapsedTimer(); self._clock.start()
        self._timer=QTimer(self); self._timer.setInterval(140); self._timer.timeout.connect(self.update)
        self._timer.start()

    def hideEvent(self,ev):
        self._timer.stop(); super().hideEvent(ev)

    def showEvent(self,ev):
        self._timer.start(); super().showEvent(ev)

    def resizeEvent(self,ev):
        self._scaled_base=None; super().resizeEvent(ev)

    def paintEvent(self,ev):
        painter=QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w,h=self.width(),self.height()
        if self._base and not self._base.isNull():
            if self._scaled_base is None or self._scaled_base.size()!=self.size():
                scaled=self._base.scaled(self.size(),Qt.AspectRatioMode.KeepAspectRatioByExpanding,Qt.TransformationMode.SmoothTransformation)
                x=(scaled.width()-w)//2; y=(scaled.height()-h)//2
                self._scaled_base=scaled.copy(x,y,w,h)
            painter.drawPixmap(0,0,self._scaled_base)
        else:
            painter.fillRect(self.rect(),QColor(BG))

        elapsed=self._clock.elapsed()
        for f in self.FLOWS:
            t=(elapsed*f["speed"])%1.0
            px=(f["sx"]+(f["ex"]-f["sx"])*t)*w
            py=(f["sy"]+(f["ey"]-f["sy"])*t)*h
            angle=math.degrees(math.atan2((f["ey"]-f["sy"])*h,(f["ex"]-f["sx"])*w))
            r=f["r"]*min(w,h)
            painter.save()
            painter.translate(px,py)
            painter.rotate(angle)
            painter.scale(f["elong"],1)
            outer=QRadialGradient(0,0,r)
            outer.setColorAt(0.0,QColor(255,138,30,int(f["alpha"]*255)))
            outer.setColorAt(0.42,QColor(255,138,30,int(f["alpha"]*0.28*255)))
            outer.setColorAt(1.0,QColor(255,138,30,0))
            painter.setPen(Qt.PenStyle.NoPen); painter.setBrush(outer)
            painter.drawEllipse(QPointF(0,0),r,r)
            inner=QRadialGradient(0,0,r*0.28)
            inner.setColorAt(0.0,QColor(255,180,80,int(f["alpha"]*1.5*255)))
            inner.setColorAt(1.0,QColor(255,138,30,0))
            painter.setBrush(inner)
            painter.drawEllipse(QPointF(0,0),r*0.28,r*0.28)
            painter.restore()
        super().paintEvent(ev)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config=Config(); self.logic=DofusLogic(self.config)
        self.hk=HotkeyManager(self.config,self.logic)
        self._hk=False; self._spam=False
        self.mini=MiniToolbar(self.config,self.logic,self._show_self,on_navigate=self._navigate)
        self.setWindowTitle(f"{APP_NAME}  {VERSION}")
        self.setMinimumWidth(700); self.setMinimumHeight(560)
        self.setStyleSheet(STYLE + SIDEBAR_STYLE)
        if (SKIN_DIR/"logo.png").exists(): self.setWindowIcon(QIcon(str(SKIN_DIR/"logo.png")))
        self._build_ui()
        # Char selector (rectangle)
        from char_selector import CharSelector
        self._char_selector = CharSelector()
        self._char_selector.char_selected.connect(self.logic.switch_to_name)

        if KEYBOARD_OK:
            def _guarded(fn):
                def _f():
                    if not _typing_in_app(): fn()
                return _f
            for cfg_key,default,fn in [("toggle_app_key","",self._toggle_vis),("calib_key","f4",self._open_calib)]:
                key=self.config.get(cfg_key,default)
                if key and self.config.get(f"{cfg_key}_on",True):
                    try: keyboard.add_hotkey(key,_guarded(fn))
                    except: pass
            # Char selector key (configurable)
            sel_key = self.config.get("selector_key","")
            if sel_key and self.config.get("selector_key_on",True):
                try: keyboard.add_hotkey(sel_key,_guarded(self._open_char_selector))
                except: pass
            # Raccourcis suivant/précédent/chef/etc. (HotkeyManager) — activés par
            # défaut au démarrage, comme les autres raccourcis ci-dessus. Avant, il
            # fallait cliquer manuellement sur "Raccourcis : désactivés" à chaque
            # lancement, sinon Tab/< ne faisaient rien silencieusement.
            self._toggle_hk()

    def _build_ui(self):
        from pages.mes_equipes import MesEquipesPage
        from pages.rosters import RostersPage
        from pages.presets import PresetsPage
        from pages.raccourcis import RaccourcisPage
        from pages.chasse_tresor import ChasseTresorPage
        from pages.zaap_menu import ZaapMenuPage
        from pages.automatisations_zaap import AutomatisationsZaapPage
        from pages.fenetres_scan import FenetresScanPage
        from pages.calibration import CalibrationPage

        root=_BackgroundWidget(); self.setCentralWidget(root)
        vl=QVBoxLayout(root); vl.setContentsMargins(0,0,0,0); vl.setSpacing(0)
        vl.addWidget(self._mk_header())

        # Corps : sidebar de navigation | pile de pages
        body=QWidget(); body.setStyleSheet("background:transparent;")
        bl=QHBoxLayout(body); bl.setContentsMargins(0,0,0,0); bl.setSpacing(0)

        self.sidebar=Sidebar(VERSION)
        self.sidebar.sig_navigate.connect(self._navigate)
        bl.addWidget(self.sidebar)

        self.stack=QStackedWidget(); self.stack.setStyleSheet("background:transparent;")
        self.page_mes_equipes=MesEquipesPage(self.config,self.logic)
        self.page_rosters=RostersPage(self.config,self.logic)
        self.page_presets=PresetsPage(self.config,self.logic)
        self.page_raccourcis=RaccourcisPage(self.config,self.logic,on_change=self.hk.reload)
        self.page_chasse_tresor=ChasseTresorPage(self.config,self.logic)
        self.page_zaap_menu=ZaapMenuPage(self.config,self.logic)
        self.page_automatisations_zaap=AutomatisationsZaapPage(self.config,self.logic)
        self.page_fenetres_scan=FenetresScanPage(self.config,self.logic)
        self.page_calibration=CalibrationPage(self.config,self.logic)

        self.pages={
            "mes_equipes":self.page_mes_equipes,
            "rosters":self.page_rosters,
            "presets":self.page_presets,
            "raccourcis":self.page_raccourcis,
            "chasse_tresor":self.page_chasse_tresor,
            "zaap_menu":self.page_zaap_menu,
            "automatisations_zaap":self.page_automatisations_zaap,
            "fenetres_scan":self.page_fenetres_scan,
            "calibration":self.page_calibration,
        }
        for page in self.pages.values(): self.stack.addWidget(page)
        bl.addWidget(self.stack, 1)

        vl.addWidget(body, 1)
        vl.addWidget(self._mk_status_bar())

        # Inter-pages : rester découplées, MainWindow fait le lien via signaux
        self.page_presets.preset_applied.connect(self.page_mes_equipes.refresh)
        self.page_presets.preset_applied.connect(self._on_order_changed)
        self.page_mes_equipes.order_changed.connect(self._on_order_changed)
        self.page_rosters.roster_applied.connect(self._on_order_changed)
        self.page_fenetres_scan.accounts_changed.connect(self._on_accounts_changed)
        self.page_automatisations_zaap.open_calibration.connect(lambda: self._open_calib_mode("zaap"))
        self.page_calibration.open_calibration.connect(self._open_calib_mode)

        self._navigate("mes_equipes")
        self._update_tag=""; self._update_url=""; self._new_exe_path=None
        QTimer.singleShot(3000,self._check_update)

    # ── Auto-update ──────────────────────────────────────────────────────────
    def _check_update(self):
        self._checker=UpdateCheckThread(VERSION)
        self._checker.done.connect(self._on_update_checked)
        self._checker.start()

    def _on_update_checked(self,tag,url,size):
        if not tag: return
        self._update_tag=tag; self._update_url=url
        if can_self_update():
            self.version_btn.setText(f"⬇ {tag} disponible")
            self._paint_version_btn(GOLD)
            try: self.version_btn.clicked.disconnect()
            except Exception: pass
            self.version_btn.clicked.connect(self._start_update_download)
        else:
            self.version_btn.setText(f"⬇ {tag} disponible (git pull)")
            self._paint_version_btn(GOLD)

    def _start_update_download(self):
        if not self._update_url: return
        try: self.version_btn.clicked.disconnect()
        except Exception: pass
        self.version_btn.setText("⏳ Téléchargement… 0%")
        self._paint_version_btn(BLUE)
        dest=APP_DIR/"DofusTeam_new.exe"
        self._downloader=UpdateDownloadThread(self._update_url,dest)
        self._downloader.progress.connect(lambda p: self.version_btn.setText(f"⏳ Téléchargement… {p}%"))
        self._downloader.done.connect(self._on_update_downloaded)
        self._downloader.start()

    def _on_update_downloaded(self,ok,err):
        if not ok:
            self.version_btn.setText(f"{VERSION} · À jour")
            self._paint_version_btn(GREEN)
            return
        self._new_exe_path=APP_DIR/"DofusTeam_new.exe"
        self.version_btn.setText(f"🔄 Redémarrer pour appliquer {self._update_tag}")
        self._paint_version_btn(ACC)
        self.version_btn.clicked.connect(self._apply_update)

    def _apply_update(self):
        if self._new_exe_path:
            apply_update_and_restart(self._new_exe_path)

    def _paint_version_btn(self,color):
        self.version_btn.setStyleSheet(f"background:rgba({self._to_rgb(color)},0.12);color:{color};border:1px solid rgba({self._to_rgb(color)},0.3);border-radius:5px;padding:2px 10px;margin-top:2px;")

    @staticmethod
    def _to_rgb(hexcolor):
        h=hexcolor.lstrip("#")
        return ",".join(str(int(h[i:i+2],16)) for i in (0,2,4))

    def _navigate(self,page_key):
        from sidebar import NON_PAGE_KEYS
        if page_key in NON_PAGE_KEYS:
            if page_key=="parametres": self._settings()
            return
        page=self.pages.get(page_key)
        if page is None: return
        self.stack.setCurrentWidget(page)
        self.sidebar.set_active(page_key)

    # ── Header ────────────────────────────────────────────────────────────────
    def _mk_header(self):
        w=QWidget(); w.setObjectName("Header"); w.setStyleSheet(f"QWidget#Header{{background:{BG2};border-bottom:1px solid rgba(255,255,255,0.06);}}"); w.setFixedHeight(70)
        lay=QHBoxLayout(w); lay.setContentsMargins(20,0,20,0); lay.setSpacing(12)

        # Logo — load_icon() recadre la marge transparente du PNG source, sinon
        # le logo ressort visiblement plus petit que les autres icônes une fois
        # mis à l'échelle (même souci que les icônes de la mini-toolbar).
        logo=QLabel()
        icon=load_icon("logo.png",40)
        if icon:
            logo.setPixmap(icon.pixmap(40,40))
        lay.addWidget(logo)

        # Title
        tl=QLabel(f"<span style='color:{TEXT};'>Dofus</span><span style='color:{ACC};'>Team</span>")
        tl.setStyleSheet(
            "font-family:'Poppins','Trebuchet MS','Century Gothic','Segoe UI',sans-serif;"
            "font-size:21px;font-weight:800;letter-spacing:-0.5px;background:transparent;"
        )
        lay.addWidget(tl)

        self.version_btn=QPushButton(f"{VERSION} · À jour")
        self.version_btn.setFont(mono(9))
        self.version_btn.setFixedHeight(22)
        self.version_btn.setCursor(Qt.CursorShape.ArrowCursor)
        self._paint_version_btn(GREEN)
        lay.addWidget(self.version_btn)
        lay.addStretch()

        # Raccourcis — un seul bouton bascule, l'état est porté par sa couleur/texte
        self.hk_btn = QPushButton("Raccourcis : désactivés")
        self.hk_btn.setFixedHeight(30)
        self.hk_btn.setToolTip("Active / désactive les raccourcis clavier (suivant, précédent, chef...)")
        self.hk_btn.setStyleSheet(f"background:transparent;color:{MUT};border:1px solid {BORDER};border-radius:6px;padding:0 12px;font-size:11px;")
        self.hk_btn.clicked.connect(self._toggle_hk); lay.addWidget(self.hk_btn)

        # Settings
        s=QPushButton("⚙"); s.setFixedSize(34,34)
        s.setStyleSheet(f"background:{BG3};border:1px solid {BORDER};border-radius:6px;font-size:14px;")
        s.clicked.connect(self._settings); lay.addWidget(s)
        return w

    # ── Status Bar ────────────────────────────────────────────────────────────
    def _sb_sep(self):
        line=QFrame(); line.setFrameShape(QFrame.Shape.VLine)
        line.setStyleSheet("background:rgba(255,255,255,0.08);border:none;")
        line.setFixedWidth(1); line.setFixedHeight(14)
        return line

    def _mk_status_bar(self):
        w=QWidget(); w.setObjectName("StatusBar"); w.setStyleSheet(f"QWidget#StatusBar{{background:{BG};border-top:1px solid rgba(255,255,255,0.05);}}"); w.setFixedHeight(34)
        lay=QHBoxLayout(w); lay.setContentsMargins(20,0,14,0); lay.setSpacing(10)

        self._sb_dot=QLabel("●"); self._sb_dot.setStyleSheet(f"color:{MUT};font-size:8px;")
        lay.addWidget(self._sb_dot)
        self._sb_conn=QLabel("Dofus non détecté"); self._sb_conn.setFont(mono(9)); self._sb_conn.setStyleSheet(f"color:{MUT};")
        lay.addWidget(self._sb_conn)
        lay.addWidget(self._sb_sep())

        self._sb_wincount=QLabel("0 fenêtre(s) détectée(s)"); self._sb_wincount.setFont(mono(9)); self._sb_wincount.setStyleSheet(f"color:{MUT};")
        lay.addWidget(self._sb_wincount)
        lay.addWidget(self._sb_sep())

        self.scan_msg=QLabel("Prêt — Lance un scan pour détecter les personnages")
        self.scan_msg.setFont(mono(9)); self.scan_msg.setStyleSheet(f"color:{MUT};")
        lay.addWidget(self.scan_msg)

        lay.addStretch()

        self._sb_last_scan=QLabel("Aucun scan encore"); self._sb_last_scan.setFont(mono(9)); self._sb_last_scan.setStyleSheet(f"color:{MUT};")
        lay.addWidget(self._sb_last_scan)

        refresh=QPushButton("⟳"); refresh.setFixedSize(22,22); refresh.setToolTip("Relancer un scan des fenêtres")
        refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh.setStyleSheet(f"background:transparent;color:{MUT};border:none;font-size:13px;")
        refresh.clicked.connect(lambda: self.page_fenetres_scan._scan())
        lay.addWidget(refresh)
        lay.addWidget(self._sb_sep())

        self._sb_clock=QLabel(""); self._sb_clock.setFont(mono(9)); self._sb_clock.setStyleSheet(f"color:{MUT};")
        lay.addWidget(self._sb_clock)
        lay.addWidget(self._sb_sep())

        hide=QPushButton("Mini-toolbar  ↓"); hide.setStyleSheet(f"background:transparent;color:{MUT};border:none;font-size:11px;")
        hide.clicked.connect(self._hide_to_mini); lay.addWidget(hide)

        self._last_scan_ts=None
        self._sb_timer=QTimer(self); self._sb_timer.setInterval(1000); self._sb_timer.timeout.connect(self._tick_status_bar)
        self._sb_timer.start()
        self._tick_status_bar()
        return w

    def _tick_status_bar(self):
        self._sb_clock.setText(time.strftime("%H:%M"))
        accounts=self.logic.all_accounts or []
        live=len([a for a in accounts if a.get("hwnd")])
        connected=live>0
        self._sb_dot.setStyleSheet(f"color:{GREEN if connected else MUT};font-size:8px;")
        self._sb_conn.setText("Dofus connecté" if connected else "Dofus non détecté")
        self._sb_conn.setStyleSheet(f"color:{TEXT};font-weight:600;" if connected else f"color:{MUT};")
        self._sb_wincount.setText(f"{live} fenêtre(s) détectée(s)")
        if self._last_scan_ts is None:
            self._sb_last_scan.setText("Aucun scan encore")
        else:
            secs=int(time.time()-self._last_scan_ts)
            if secs<60: txt=f"il y a {secs}s"
            elif secs<3600: txt=f"il y a {secs//60} min"
            else: txt=f"il y a {secs//3600} h"
            self._sb_last_scan.setText(f"Dernier scan : {txt}")

    # ── Account management ────────────────────────────────────────────────────
    def _on_accounts_changed(self,accounts):
        """Branché sur FenetresScanPage.accounts_changed — tient la mini-toolbar
        et les autres pages à jour sans dépendance directe entre elles."""
        self.mini._rebuild_char_icons(accounts)
        self.page_mes_equipes.refresh()
        self.page_chasse_tresor._refresh_accounts()
        self._last_scan_ts=time.time()
        self._tick_status_bar()

    def _on_order_changed(self):
        """Branché sur preset_applied (page Presets) et order_changed (page Mes
        équipes) — l'application d'un preset trie déjà la barre des tâches
        Windows et l'ordre d'initiative via DofusLogic.apply_preset(), mais la
        bande d'avatars de la mini-toolbar n'était sinon reconstruite qu'après
        un scan : on la rafraîchit ici pour qu'elle suive le nouvel ordre."""
        self.mini._rebuild_char_icons(self.logic.get_cycle_list())

    # ── Actions ───────────────────────────────────────────────────────────────
    def _toggle_hk(self):
        self._hk=not self._hk
        if self._hk:
            self.hk.enable()
            self.hk_btn.setText("Raccourcis : activés")
            self.hk_btn.setStyleSheet(f"background:rgba(63,185,80,0.1);color:{GREEN};border:1px solid rgba(63,185,80,0.3);border-radius:6px;padding:0 12px;font-size:11px;font-weight:600;")
            self.scan_msg.setText("✅  Raccourcis actifs — " + (self.config.get("next_key","?") or "?") + " = perso suivant")
        else:
            self.hk.disable()
            self.hk_btn.setText("Raccourcis : désactivés")
            self.hk_btn.setStyleSheet(f"background:transparent;color:{MUT};border:1px solid {BORDER};border-radius:6px;padding:0 12px;font-size:11px;")

    def _hide_to_mini(self): self.hide(); self.mini.show(); self.mini.raise_()
    def _show_self(self): self.mini.hide(); self.show(); self.raise_(); self.activateWindow()
    def _toggle_vis(self):
        if self.isVisible(): self._hide_to_mini()
        else: self._show_self()

    def _open_char_selector(self):
        accounts = self.logic.get_cycle_list()
        if not accounts: return
        current = None
        lst = self.logic.get_cycle_list()
        if 0 <= self.logic._idx < len(lst): current = lst[self.logic._idx]["name"]
        self._char_selector.show_for(accounts, current)

    def _open_calib(self): self._open_calib_mode("zaap","")

    def _open_calib_mode(self, mode, target_name=""):
        from calibrator import CalibrationManager
        label = {"zaap":"Zaap","chat":"Chat","inventaire":"Inventaire"}.get(mode, mode)
        if target_name:
            label = f"{label} — {target_name}"
        if not self.logic.scan_slots():
            QMessageBox.warning(self,f"Calibration {label}","Aucune fenêtre Dofus.\nOuvrez Dofus et scannez d'abord."); return
        self._calib_mgr=CalibrationManager(self.config,self.logic,self,mode=mode,target_name=target_name or None)
        self._calib_mgr.status.connect(lambda m: self.scan_msg.setText(m[:60]))
        def _done():
            self.scan_msg.setText(f"✅  {label} calibré")
            self.scan_msg.setStyleSheet(f"color:{GREEN}; font-weight:700;")
            QTimer.singleShot(1500, lambda: self.scan_msg.setStyleSheet(f"color:{MUT};"))
            self.page_fenetres_scan._refresh()
            self.page_calibration.refresh(just_calibrated=target_name)
        self._calib_mgr.finished.connect(_done)
        self._calib_mgr.start()

    def _settings(self):
        dlg=QDialog(self); dlg.setWindowTitle("Paramètres avancés"); dlg.setMinimumSize(520,420); dlg.setStyleSheet(STYLE)
        lay=QVBoxLayout(dlg); lay.setContentsMargins(22,20,22,20); lay.setSpacing(16)

        title=QLabel("⌨ Raccourcis de cycle rapide")
        title.setStyleSheet(f"color:{TEXT}; font-size:15px; font-weight:700; background:transparent;")
        lay.addWidget(title)
        sub=QLabel("Ctrl+F1 à Ctrl+F8 — bascule directement sur le personnage du slot correspondant.")
        sub.setWordWrap(True)
        sub.setStyleSheet(f"color:{MUT}; font-size:11.5px; background:transparent;")
        lay.addWidget(sub)

        binds=self.config.get("cycle_row_binds",[]); grid=QGridLayout()
        grid.setHorizontalSpacing(18); grid.setVerticalSpacing(14)
        inps=[]
        for i in range(8):
            cell=QWidget(); cl=QVBoxLayout(cell); cl.setContentsMargins(0,0,0,0); cl.setSpacing(4)
            lbl=QLabel(f"SLOT {i+1}")
            lbl.setStyleSheet(f"color:{MUT}; font-size:10.5px; font-weight:700; letter-spacing:1px; background:transparent;")
            cl.addWidget(lbl)
            inp=QLineEdit(binds[i] if i<len(binds) else "")
            inp.setFixedHeight(32)
            inp.setAlignment(Qt.AlignmentFlag.AlignCenter)
            inp.setPlaceholderText("—")
            inp.setStyleSheet(
                f"background:{BG3}; border:1px solid {BORDER}; border-radius:6px;"
                f"padding:4px 8px; font-size:13px; color:{ACC}; font-family:'Space Mono'; font-weight:700;"
            )
            cl.addWidget(inp)
            grid.addWidget(cell,i//4,i%4)
            inps.append(inp)
        lay.addLayout(grid)

        lay.addWidget(section_label("AUTRES RÉGLAGES"))
        sr=QHBoxLayout(); sr.setSpacing(10)
        sr_lbl=QLabel("Intervalle spam clic (s) :")
        sr_lbl.setStyleSheet(f"color:{TEXT}; font-size:12px; background:transparent;")
        sr.addWidget(sr_lbl)
        si=QLineEdit(str(self.config.get("spam_click_interval",0.1))); si.setFixedWidth(70); si.setFixedHeight(30)
        sr.addWidget(si); sr.addStretch()
        lay.addLayout(sr)

        lay.addStretch()
        sv=accent_btn("💾  Sauvegarder",lambda:None)
        sv.setFixedHeight(38)
        def _sv():
            self.config.set("cycle_row_binds",[i.text().strip() for i in inps])
            try: self.config.set("spam_click_interval",float(si.text()))
            except: pass
            self.config.save(); (self.hk.reload() if self._hk else None); dlg.close()
        sv.clicked.disconnect(); sv.clicked.connect(_sv); lay.addWidget(sv); dlg.exec()

    def closeEvent(self,e): self._spam=False; self.hk.disable(); self.config.save(); e.accept()
    def keyPressEvent(self,e):
        pass  # No Escape handling - avoid accidental window switches

# ── Tray ──────────────────────────────────────────────────────────────────────
class AppTray(QSystemTrayIcon):
    def __init__(self,app,window):
        super().__init__(app); self.window=window
        pix=QPixmap(32,32); pix.fill(QColor(ACC))
        icon=load_icon("logo.png",32)
        if icon: pix=icon.pixmap(32,32)
        self.setIcon(QIcon(pix)); self.setToolTip(f"{APP_NAME} {VERSION}")
        menu=QMenu(); menu.setStyleSheet(STYLE)
        menu.addAction("▸  Afficher").triggered.connect(window._show_self)
        menu.addAction("▪  Cacher").triggered.connect(window._hide_to_mini)
        menu.addSeparator(); menu.addAction("✕  Quitter").triggered.connect(QApplication.quit)
        self.setContextMenu(menu); self.activated.connect(lambda r: window._show_self() if r==QSystemTrayIcon.ActivationReason.DoubleClick else None)
        self.show()

# ── Entry ─────────────────────────────────────────────────────────────────────
def main():
    if sys.platform == "win32":
        # Sans AppUserModelID explicite, Windows regroupe le process sous une
        # icône générique dans la barre des tâches (le systray, lui, s'affiche
        # correctement car QSystemTrayIcon fixe son icône indépendamment).
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(f"DofusTeam.Organizer.{VERSION}")
        except Exception:
            pass
    tk_root=tk.Tk(); tk_root.withdraw()
    app=QApplication(sys.argv); app.setApplicationName(APP_NAME); app.setQuitOnLastWindowClosed(False)
    if (SKIN_DIR/"logo.png").exists(): app.setWindowIcon(QIcon(str(SKIN_DIR/"logo.png")))
    window=MainWindow(); window.show(); tray=AppTray(app,window)

    from radial_menu import RadialMenuController
    radial=RadialMenuController(tk_root,window.config,window.logic,SKIN_DIR)
    radial.enable()

    def _tk():
        while True:
            try:
                radial.poll(); tk_root.update(); time.sleep(0.016)
            except: break
    threading.Thread(target=_tk,daemon=True).start(); sys.exit(app.exec())

if __name__=="__main__": main()
