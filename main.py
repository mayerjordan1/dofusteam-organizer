#!/usr/bin/env python3
"""
DofusTeam — Beta V1.01
Gestionnaire multi-compte Dofus Unity
"""
import sys, json, threading, time, ctypes, random
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
                    STYLE, mono, section_label, card, accent_btn, ghost_btn, make_avatar)

APP_NAME = "DofusTeam"
VERSION  = "Beta V1.01"

CLASSES = ["Cra","Ecaflip","Eliotrope","Eniripsa","Enutrof","Feca","Forgelance",
           "Huppermage","Iop","Osamodas","Ouginak","Pandawa","Roublard","Sacrieur",
           "Sadida","Sram","Steamer","Xelor","Zobal"]
TEAMS = ["", "Team 1", "Team 2", "Team 3", "Team 4"]

# ── Settings ──────────────────────────────────────────────────────────────────
DEFAULT = {
    "prev_key":"<","next_key":"tab","leader_key":"","sync_key":"decimal",
    "toggle_app_key":"f10","refresh_key":"f5","sort_taskbar_key":"","calib_key":"f4",
    "auto_zaap_key":"","invite_group_key":"","paste_active_key":"",
    "zaap_open_delay":0.8,"zaap_click_delay":0.5,"zaap_paste_delay":0.4,
    "game_haven_key":"h","game_version":"Unity","selector_key":"","zaap_favorites":[],"zaap_paste_delay":0.35,
    "leader_name":"","accounts_state":{},"accounts_team":{},
    "current_mode":"ALL","classes":{},"custom_order":[],
    "macro_positions":{"chat_position":None,"zaaps":{}},
    "cycle_row_binds":["ctrl+F1","ctrl+F2","ctrl+F3","ctrl+F4","ctrl+F5","ctrl+F6","ctrl+F7","ctrl+F8"],
    "volume_level":50,"spam_click_interval":0.1,
    "mini_toolbar_x":100,"mini_toolbar_y":100,
    "presets":[],
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
            team=self.config.get("accounts_team",{}).get(pseudo,"Team 1")
            accounts.append({"name":pseudo,"hwnd":hwnd,"active":active,"team":team,"classe":cls})
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
        mode=self.config.get("current_mode","ALL")
        return [a for a in self.all_accounts if a["active"] and (mode=="ALL" or a["team"]==mode)]

    def focus_window(self,hwnd):
        if not hwnd or not WINDOWS: return
        try:
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd,win32con.SW_RESTORE)
            # AttachThreadInput: proper focus steal, no Alt key = no Alt+Tab
            fg = win32gui.GetForegroundWindow()
            if fg == hwnd: return  # already focused
            fg_tid  = ctypes.windll.user32.GetWindowThreadProcessId(fg, None)
            cur_tid = ctypes.windll.user32.GetWindowThreadProcessId(hwnd, None)
            if fg_tid != cur_tid:
                ctypes.windll.user32.AttachThreadInput(fg_tid, cur_tid, True)
            ctypes.windll.user32.AllowSetForegroundWindow(0xFFFFFFFF)
            win32gui.SetForegroundWindow(hwnd)
            win32gui.BringWindowToTop(hwnd)
            if fg_tid != cur_tid:
                ctypes.windll.user32.AttachThreadInput(fg_tid, cur_tid, False)
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

    def set_team(self,name,team):
        for a in self.all_accounts:
            if a["name"]==name: a["team"]=team
        t=self.config.get("accounts_team",{})
        if team: t[name]=team
        else: t.pop(name,None)
        self.config.set("accounts_team",t); self.config.save()

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

    def close_all(self):
        for a in self.get_cycle_list():
            try:
                _,pid=win32process.GetWindowThreadProcessId(a["hwnd"])
                h=ctypes.windll.kernel32.OpenProcess(1,False,pid)
                ctypes.windll.kernel32.TerminateProcess(h,0); ctypes.windll.kernel32.CloseHandle(h)
            except: pass

    def paste_active(self):
        """Colle + valide (Ctrl+V, Entrée) sur la fenêtre Dofus actuellement au premier plan,
        après un clic sur la position de chat calibrée. Ne fait rien si la fenêtre active
        n'est pas un compte Dofus connu (évite tout effet de bord ailleurs)."""
        if not WINDOWS or not PYAUTOGUI_OK: return
        try:
            fg=win32gui.GetForegroundWindow()
        except Exception: return
        if not any(a["hwnd"]==fg for a in self.all_accounts): return
        cp=self.config.get("macro_positions",{}).get("chat_position")
        if not cp: return
        def _do():
            try:
                pyautogui.click(cp[0],cp[1]); time.sleep(0.15)
                pyautogui.hotkey("ctrl","v"); time.sleep(0.08)
                pyautogui.press("enter")
            except Exception as e:
                print(f"[paste_active] {e}")
        threading.Thread(target=_do,daemon=True).start()

# ── Hotkeys ───────────────────────────────────────────────────────────────────
class HotkeyManager:
    def __init__(self,config,logic): self.config=config; self.logic=logic; self.active=False
    def enable(self):
        if not KEYBOARD_OK or self.active: return
        self.active=True; self._reg_all()
    def disable(self):
        if not self.active: return
        self.active=False
        try: keyboard.unhook_all_hotkeys()
        except: pass
    def reload(self): was=self.active; self.disable(); was and self.enable()
    def _reg(self,key,fn):
        if key:
            try: keyboard.add_hotkey(key,fn,suppress=False)
            except Exception as e: print(f"[HK] {key}: {e}")
    def _reg_all(self):
        c=self.config
        self._reg(c.get("next_key"),self.logic.switch_next)
        self._reg(c.get("prev_key"),self.logic.switch_prev)
        self._reg(c.get("leader_key"),self.logic.switch_to_leader)
        self._reg(c.get("refresh_key"),self.logic.refresh_all)
        self._reg(c.get("sort_taskbar_key"),self.logic.sort_taskbar)
        self._reg(c.get("paste_active_key"),self.logic.paste_active)
        for i,b in enumerate(c.get("cycle_row_binds",[])):
            self._reg(b,lambda idx=i: self.logic.switch_to_index(idx))

# ── Account Row ───────────────────────────────────────────────────────────────
class AccountRow(QFrame):
    sig_remove=pyqtSignal(str); sig_up=pyqtSignal(str); sig_down=pyqtSignal(str); sig_leader=pyqtSignal(str)

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

        # Avatar — no border, no background
        av = QLabel()
        av.setFixedSize(28,28)
        av.setAlignment(Qt.AlignmentFlag.AlignCenter)
        av.setAutoFillBackground(False)
        av.setStyleSheet("background:transparent;border:none;")
        pix = make_avatar(acc.get("classe",""), 26)
        if pix: av.setPixmap(pix)
        else: av.setText("?"); av.setStyleSheet(f"color:{MUT};font-size:13px;background:transparent;")
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

        # Team badge
        team = config.get("accounts_team",{}).get(name,"")
        self.tb = QPushButton(team.replace("Team ","T") if team else "—")
        self.tb.setFixedSize(30,24)
        self.tb.setToolTip("Changer d'équipe"); self.tb.clicked.connect(lambda: self._cycle_team(name)); lay.addWidget(self.tb)
        self._style_team_badge(bool(team))

        # Star — accent quand chef
        is_leader = config.get("leader_name") == name
        self.star = icon_btn("★", "Définir comme chef", active=is_leader, active_color=GOLD)
        self.star.clicked.connect(lambda: self.sig_leader.emit(name)); lay.addWidget(self.star)

        # Remove
        rm = icon_btn("✕", "Retirer de la liste", size=(26,24))
        rm.clicked.connect(lambda: self.sig_remove.emit(name)); lay.addWidget(rm)

    def _style_team_badge(self, active):
        tc = BLUE if active else MUT
        bg = "rgba(79,163,224,0.14)" if active else "transparent"
        self.tb.setStyleSheet(f"QPushButton{{background:{bg};color:{tc};border:none;border-radius:5px;font-size:10px;font-weight:700;}}QPushButton:hover{{background:rgba(255,255,255,0.06);}}")

    def _cycle_team(self,name):
        cur=self.config.get("accounts_team",{}).get(name,"")
        idx=TEAMS.index(cur) if cur in TEAMS else 0; new=TEAMS[(idx+1)%len(TEAMS)]
        t=self.config.get("accounts_team",{})
        if new: t[name]=new
        else: t.pop(name,None)
        self.config.set("accounts_team",t); self.config.save()
        self.tb.setText(new.replace("Team ","T") if new else "—")
        self._style_team_badge(bool(new))

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
        for i,p in enumerate(presets):
            row=QWidget(); rl=QHBoxLayout(row); rl.setContentsMargins(8,4,8,4); rl.setSpacing(8)
            row.setStyleSheet(f"background:{BG2};border-radius:6px;")
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
    def __init__(self,config,idx,parent=None):
        super().__init__(parent); self.config=config; self.idx=idx
        presets=self.config.get("presets",[])
        self.preset=presets[idx].copy() if idx>=0 and idx<len(presets) else {"name":"","order":[]}
        self.setWindowTitle("Preset d'initiative"); self.setFixedSize(360,480); self.setStyleSheet(STYLE)
        self._build()

    def _build(self):
        lay=QVBoxLayout(self); lay.setContentsMargins(16,16,16,16); lay.setSpacing(12)
        lay.addWidget(QLabel("Nom du preset :"))
        self.name_inp=QLineEdit(self.preset.get("name","")); self.name_inp.setPlaceholderText("Ex: Farm Abysse"); lay.addWidget(self.name_inp)
        lay.addWidget(QLabel("Ordre des personnages (▲▼ pour réordonner) :"))

        # List of all known chars with checkboxes + reorder
        self.scroll=QScrollArea(); self.scroll.setWidgetResizable(True)
        self.container=QWidget(); self.vlay=QVBoxLayout(self.container)
        self.vlay.setContentsMargins(0,0,0,0); self.vlay.setSpacing(3)
        self.scroll.setWidget(self.container); lay.addWidget(self.scroll)
        self._build_char_list()

        btns=QHBoxLayout()
        cancel=ghost_btn("Annuler",self.reject); btns.addWidget(cancel)
        save=accent_btn("💾 Sauvegarder",self._save); btns.addWidget(save)
        lay.addLayout(btns)

    def _build_char_list(self):
        while self.vlay.count():
            item=self.vlay.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        all_known=self.config.get("custom_order",[])
        preset_order=self.preset.get("order",[])
        # Show preset order first, then unselected
        ordered=[n for n in preset_order if n in all_known]+[n for n in all_known if n not in preset_order]
        self.rows=[]
        for name in ordered:
            row=QWidget(); rl=QHBoxLayout(row); rl.setContentsMargins(4,2,4,2); rl.setSpacing(6)
            chk=QCheckBox(); chk.setChecked(name in preset_order); rl.addWidget(chk)
            av=QLabel(); av.setFixedSize(24,24)
            pix=make_avatar(self.config.get("classes",{}).get(name,""),24)
            if pix: av.setPixmap(pix)
            rl.addWidget(av)
            lbl=QLabel(name); lbl.setStyleSheet(f"font-weight:600;color:{TEXT};"); rl.addWidget(lbl)
            rl.addStretch()
            for sym,d in [("▲",-1),("▼",1)]:
                b=QPushButton(sym); b.setFixedSize(20,20); b.setStyleSheet(f"background:{BG3};border:none;border-radius:3px;color:{MUT};font-size:8px;")
                b.clicked.connect(lambda _,n=name,dv=d: self._move(n,dv)); rl.addWidget(b)
            self.vlay.addWidget(row)
            self.rows.append((name,chk,row))

    def _move(self,name,d):
        names=[r[0] for r in self.rows]; idx=names.index(name); new=idx+d
        if 0<=new<len(self.rows):
            self.rows[idx],self.rows[new]=self.rows[new],self.rows[idx]
            # Rebuild visually
            for _,_,w in self.rows:
                self.vlay.removeWidget(w)
            for _,_,w in self.rows:
                self.vlay.addWidget(w)

    def _save(self):
        name=self.name_inp.text().strip()
        if not name: return
        order=[r[0] for r in self.rows if r[1].isChecked()]
        preset={"name":name,"order":order}
        presets=self.config.get("presets",[])
        if self.idx>=0 and self.idx<len(presets): presets[self.idx]=preset
        else: presets.append(preset)
        self.config.set("presets",presets); self.config.save()
        self.saved.emit(); self.accept()

# ── Mini Toolbar ──────────────────────────────────────────────────────────────
class MiniToolbar(QWidget):
    def __init__(self,config,logic,on_show):
        super().__init__(None,Qt.WindowType.Tool|Qt.WindowType.FramelessWindowHint|Qt.WindowType.WindowStaysOnTopHint)
        self.config=config; self.logic=logic; self.on_show=on_show; self._spam=False; self._drag=None
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        bar=QWidget(self); bar.setObjectName("b")
        bar.setStyleSheet(f"QWidget#b{{background:{BG};border:1px solid rgba(255,138,30,0.35);border-radius:10px;}}")
        lay=QHBoxLayout(bar); lay.setContentsMargins(10,7,10,7); lay.setSpacing(6)
        def mkb(icon,tip,color=BG3,ck=False):
            b=QPushButton(icon); b.setFixedSize(36,34); b.setToolTip(tip); b.setCheckable(ck)
            b.setStyleSheet(f"QPushButton{{background:{color};color:white;border:none;border-radius:6px;font-size:15px;}}QPushButton:checked{{background:{ACC};color:#0f1115;}}")
            return b
        self.b_show=mkb("🥚","Afficher DofusTeam")
        self.b_prev=mkb("◀","Perso précédent")
        self.b_next=mkb("▶","Perso suivant")
        self.b_leader=mkb("⭐","Aller au chef",GOLD)
        self.b_hsac=mkb("🏠","Havre-sac + Zaap\n1. Appuie H sur tous les persos\n2. Clique zaap calibré sur tous",GOLD)
        self.b_paste=mkb("📋","Coller destination zaap\nCtrl+A + Ctrl+V + Entrée sur tous les persos\n(copie la destination d'abord !)")
        self.b_spam=mkb("🖱","Spam Click",ck=True)
        self.b_show.clicked.connect(lambda:(self.hide(),self.on_show()))
        self.b_prev.clicked.connect(lambda: self.logic.switch_prev() if self.logic else None)
        self.b_next.clicked.connect(lambda: self.logic.switch_next() if self.logic else None)
        self.b_leader.clicked.connect(lambda: self.logic.switch_to_leader() if self.logic else None)
        self.b_hsac.clicked.connect(self._quick_hsac)
        self.b_hsac.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.b_hsac.customContextMenuRequested.connect(lambda: self._show_zaap_menu())
        self.b_hsac.setToolTip("🏠 Havre-sac + Zaap\nClic gauche: ouvrir tous les havresacs\nClic droit: zaap favoris ⭐")
        self.b_paste.clicked.connect(self._quick_paste)
        self.b_spam.toggled.connect(self._toggle_spam)
        for w in (self.b_show,self.b_prev,self.b_next,self.b_leader,self.b_hsac,self.b_paste,self.b_spam): lay.addWidget(w)
        self._inner_lay = lay  # store ref for char icons
        self._char_btns = []; self._char_sep = None
        bar.adjustSize(); self.resize(bar.sizeHint().width()+20,bar.sizeHint().height()+14); bar.move(10,7)
        self.move(config.get("mini_toolbar_x",100),config.get("mini_toolbar_y",100))

    def update_focus(self,name): self.focus_lbl.setText(name[:10] if name else "—")
    def _quick_zaap(self):
        if not PYAUTOGUI_OK or not self.logic: return
        try:
            from zaap_macro import ZaapExecutor
            ZaapExecutor(self.config,self.logic,on_status=lambda m:print(f"[zaap]{m}")).start()
        except: pass

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
        from zaap_favorites import ZaapFavoritesDialog
        ZaapFavoritesDialog(self.config, self).exec()

    def _rebuild_char_icons(self, accounts):
        """Rebuild character icon strip after scan."""
        # Remove old char buttons
        for b in getattr(self, '_char_btns', []):
            b.deleteLater()
        self._char_btns = []
        # Remove old separator
        if hasattr(self, '_char_sep') and self._char_sep:
            self._char_sep.deleteLater(); self._char_sep = None

        if not accounts or not hasattr(self, '_inner_lay'): return

        # Add separator
        sep = QFrame(); sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet("color:rgba(255,255,255,0.1); max-height:30px;")
        sep.setFixedHeight(30)
        self._inner_lay.addWidget(sep); self._char_sep = sep

        for acc in accounts:
            b = QPushButton(); b.setFixedSize(34,34); b.setToolTip(acc["name"])
            pix = make_avatar(acc.get("classe",""), 28)
            if pix: b.setIcon(QIcon(pix)); b.setIconSize(QSize(28,28))
            b.setStyleSheet(
                f"QPushButton{{background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.08);border-radius:6px;}}"
                f"QPushButton:hover{{background:rgba(255,138,30,0.15);border-color:#ff8a1e;}}"
            )
            b.clicked.connect(lambda _, n=acc["name"]: self.logic.switch_to_name(n) if self.logic else None)
            self._inner_lay.addWidget(b); self._char_btns.append(b)

        # Timer to highlight currently focused character
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
                    f"QPushButton{{background:{'rgba(255,138,30,0.2)' if is_active else 'rgba(255,255,255,0.05)'};border:{'2px solid #ff8a1e' if is_active else '1px solid rgba(255,255,255,0.08)'};border-radius:6px;}}"
                    f"QPushButton:hover{{background:rgba(255,138,30,0.15);border-color:#ff8a1e;}}"
                )

    def _quick_paste(self):
        if not PYAUTOGUI_OK or not self.logic: return
        from zaap_macro import quick_paste_zaap
        quick_paste_zaap(self.config, self.logic, on_status=lambda m:print(f"[paste]{m}"))
    def _toggle_spam(self,on):
        if not PYAUTOGUI_OK: self.b_spam.setChecked(False); return
        self._spam=on
        if on:
            iv=self.config.get("spam_click_interval",0.1)
            def _s():
                while self._spam: pyautogui.click(); time.sleep(iv)
            threading.Thread(target=_s,daemon=True).start()
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
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config=Config(); self.logic=DofusLogic(self.config)
        self.hk=HotkeyManager(self.config,self.logic)
        self._hk=False; self._spam=False
        self.mini=MiniToolbar(self.config,self.logic,self._show_self)
        self.setWindowTitle(f"{APP_NAME}  {VERSION}")
        self.setMinimumWidth(700); self.setMinimumHeight(560)
        self.setStyleSheet(STYLE)
        if (SKIN_DIR/"logo.png").exists(): self.setWindowIcon(QIcon(str(SKIN_DIR/"logo.png")))
        self._build_ui()
        # Char selector (rectangle)
        from char_selector import CharSelector
        self._char_selector = CharSelector()
        self._char_selector.char_selected.connect(self.logic.switch_to_name)

        if KEYBOARD_OK:
            for key,fn in [(self.config.get("toggle_app_key"),self._toggle_vis),(self.config.get("calib_key","f4"),self._open_calib)]:
                if key:
                    try: keyboard.add_hotkey(key,fn)
                    except: pass
            # Char selector key (configurable)
            sel_key = self.config.get("selector_key","")
            if sel_key:
                try: keyboard.add_hotkey(sel_key,self._open_char_selector)
                except: pass

    def _build_ui(self):
        root=QWidget(); self.setCentralWidget(root)
        vl=QVBoxLayout(root); vl.setContentsMargins(0,0,0,0); vl.setSpacing(0)
        vl.addWidget(self._mk_header())
        vl.addWidget(self._mk_action_bar())
        # Main content: accounts + side panel
        main=QWidget(); ml=QHBoxLayout(main); ml.setContentsMargins(16,12,16,12); ml.setSpacing(16)
        ml.addWidget(self._mk_accounts_panel(), 6)
        ml.addWidget(self._mk_side_panel(), 4)
        vl.addWidget(main, 1)
        vl.addWidget(self._mk_shortcuts_bar())
        vl.addWidget(self._mk_status_bar())

    # ── Header ────────────────────────────────────────────────────────────────
    def _mk_header(self):
        w=QWidget(); w.setStyleSheet(f"background:{BG2};border-bottom:1px solid rgba(255,255,255,0.06);"); w.setFixedHeight(70)
        lay=QHBoxLayout(w); lay.setContentsMargins(20,0,20,0); lay.setSpacing(12)

        # Logo
        logo=QLabel()
        if (SKIN_DIR/"logo.png").exists():
            pix=QPixmap(str(SKIN_DIR/"logo.png")).scaled(40,40,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)
            logo.setPixmap(pix)
        lay.addWidget(logo)

        # Title
        tl=QLabel(APP_NAME); tl.setFont(mono(18,True)); tl.setStyleSheet(f"color:{TEXT};letter-spacing:-0.5px;")
        lay.addWidget(tl)
        vl=QLabel(VERSION); vl.setStyleSheet(f"color:{MUT};font-size:10px;margin-top:8px;"); lay.addWidget(vl)
        lay.addStretch()

        # Status badge
        self.status_badge=QLabel("○ OFFLINE")
        self.status_badge.setFont(mono(9))
        self.status_badge.setFixedHeight(24)
        self.status_badge.setStyleSheet(f"background:rgba(255,255,255,0.04);color:{MUT};border:1px solid rgba(255,255,255,0.08);border-radius:5px;padding:2px 10px;")
        lay.addWidget(self.status_badge)

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

    # ── Action Bar ────────────────────────────────────────────────────────────
    def _mk_action_bar(self):
        w=QWidget(); w.setStyleSheet(f"background:{BG};border-bottom:1px solid rgba(255,255,255,0.05);"); w.setFixedHeight(46)
        lay=QHBoxLayout(w); lay.setContentsMargins(20,0,20,0); lay.setSpacing(6)

        def flat_btn(text,tip,fn,size=(34,30)):
            b=QPushButton(text); b.setFixedSize(*size); b.setToolTip(tip)
            b.setStyleSheet(f"background:{BG3};border:1px solid {BORDER};border-radius:6px;font-size:12px;color:{TEXT};")
            b.clicked.connect(fn); return b

        # Navigation (groupe compact, usage fréquent)
        lay.addWidget(flat_btn("◀","Perso précédent",lambda: self.logic.switch_prev()))
        lay.addWidget(flat_btn("▶","Perso suivant",lambda: self.logic.switch_next()))
        lay.addWidget(flat_btn("⭐","Aller au chef",lambda: self.logic.switch_to_leader()))

        sep=QFrame(); sep.setFrameShape(QFrame.Shape.VLine); sep.setStyleSheet(f"color:{BORDER};"); lay.addWidget(sep)

        # Action principale : scanner (seul bouton accentué de la barre)
        scan_btn=QPushButton("🔍  Scanner"); scan_btn.setToolTip("Scanner les fenêtres Dofus")
        scan_btn.setStyleSheet(f"background:{ACC};color:#0f1115;border:none;border-radius:6px;padding:5px 14px;font-size:12px;font-weight:700;")
        scan_btn.clicked.connect(self._scan); lay.addWidget(scan_btn)
        lay.addWidget(ghost_btn("Trier la barre Windows",lambda: self.logic.sort_taskbar()))

        lay.addStretch()

        # Le reste : regroupé dans un seul menu pour ne pas noyer la barre
        tools_btn=QPushButton("Outils  ▾"); tools_btn.setToolTip("Auto Zaap, favoris, invitation, chasse au trésor, calibrations")
        tools_btn.setStyleSheet(f"background:{BG3};border:1px solid {BORDER};border-radius:6px;padding:5px 14px;font-size:12px;color:{TEXT};")
        menu=QMenu(tools_btn); menu.setStyleSheet(STYLE)
        menu.addAction("⚡  Auto Zaap").triggered.connect(self._open_zaap)
        menu.addAction("★  Zaap favoris").triggered.connect(self._open_zaap_favorites)
        menu.addAction("👥  Inviter le groupe").triggered.connect(self._open_invite)
        menu.addAction("🗺  Chasse au trésor").triggered.connect(self._open_hunt)
        menu.addSeparator()
        menu.addAction("🎯  Calibrer Zaap  (F4)").triggered.connect(self._open_calib_zaap)
        menu.addAction("💬  Calibrer Chat").triggered.connect(self._open_calib_chat)
        tools_btn.setMenu(menu)
        lay.addWidget(tools_btn)
        return w

    # ── Accounts Panel ────────────────────────────────────────────────────────
    def _mk_accounts_panel(self):
        w=QWidget()
        lay=QVBoxLayout(w); lay.setContentsMargins(0,0,0,0); lay.setSpacing(8)

        # Header row
        hrow=QHBoxLayout()
        hrow.addWidget(section_label("COMPTES"))
        self.count_lbl=QLabel(""); self.count_lbl.setStyleSheet(f"background:rgba(255,138,30,0.08);color:{ACC};border-radius:8px;padding:1px 8px;font-size:11px;font-family:'Space Mono';")
        hrow.addWidget(self.count_lbl); hrow.addStretch()
        add=QPushButton("+ Ajouter"); add.setStyleSheet(f"background:rgba(255,138,30,0.08);color:{ACC};border:1px solid rgba(255,138,30,0.2);border-radius:5px;padding:3px 10px;font-size:11px;"); add.clicked.connect(self._add_account); hrow.addWidget(add)
        lay.addLayout(hrow)

        # Card container
        card_w=QWidget(); card_w.setStyleSheet(f"background:{BG2};border:1px solid rgba(255,255,255,0.07);border-radius:10px;")
        card_lay=QVBoxLayout(card_w); card_lay.setContentsMargins(0,0,0,0); card_lay.setSpacing(0)

        # Empty state
        self.empty_lbl=QLabel("Aucun personnage détecté\nClique sur  🔍 SCANNER  pour démarrer")
        self.empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_lbl.setStyleSheet(f"color:{MUT};font-size:12px;padding:30px;")
        card_lay.addWidget(self.empty_lbl)

        # Scroll
        self.acct_scroll=QScrollArea(); self.acct_scroll.setWidgetResizable(True); self.acct_scroll.setVisible(False)
        self.acct_container=QWidget(); self.acct_layout=QVBoxLayout(self.acct_container)
        self.acct_layout.setContentsMargins(0,0,0,0); self.acct_layout.setSpacing(0); self.acct_layout.addStretch()
        self.acct_scroll.setWidget(self.acct_container); card_lay.addWidget(self.acct_scroll)

        lay.addWidget(card_w, 1)
        return w

    # ── Side Panel ────────────────────────────────────────────────────────────
    def _mk_side_panel(self):
        w=QWidget()
        lay=QVBoxLayout(w); lay.setContentsMargins(0,0,0,0); lay.setSpacing(14)

        # Version selector + mode
        mode_card=QWidget(); mode_card.setStyleSheet(f"background:{BG2};border:1px solid rgba(255,255,255,0.07);border-radius:10px;")
        ml=QVBoxLayout(mode_card); ml.setContentsMargins(12,10,12,10); ml.setSpacing(8)
        ml.addWidget(section_label("CONFIGURATION"))
        row1=QHBoxLayout(); row1.addWidget(QLabel("Mode :")); self.mode_c=QComboBox()
        self.mode_c.addItems(["ALL","Team 1","Team 2","Team 3","Team 4"]); self.mode_c.setCurrentText(self.config.get("current_mode","ALL"))
        self.mode_c.currentTextChanged.connect(lambda t:(self.config.set("current_mode",t),self.config.save())); row1.addWidget(self.mode_c); ml.addLayout(row1)
        row2=QHBoxLayout(); row2.addWidget(QLabel("Version :")); self.ver_c=QComboBox()
        self.ver_c.addItems(["Unity","Rétro"]); self.ver_c.setCurrentText(self.config.get("game_version","Unity"))
        self.ver_c.currentTextChanged.connect(lambda t:(self.config.set("game_version",t),self.config.save())); row2.addWidget(self.ver_c); ml.addLayout(row2)
        lay.addWidget(mode_card)

        # Presets
        preset_card=QWidget(); preset_card.setStyleSheet(f"background:{BG2};border:1px solid rgba(255,255,255,0.07);border-radius:10px;")
        pl=QVBoxLayout(preset_card); pl.setContentsMargins(12,10,12,10); pl.setSpacing(8)
        self.preset_panel=PresetPanel(self.config,self.logic)
        self.preset_panel.preset_applied.connect(self._refresh)
        pl.addWidget(self.preset_panel)
        lay.addWidget(preset_card)

        # Quick actions
        qa_card=QWidget(); qa_card.setStyleSheet(f"background:{BG2};border:1px solid rgba(255,255,255,0.07);border-radius:10px;")
        ql=QVBoxLayout(qa_card); ql.setContentsMargins(12,10,12,10); ql.setSpacing(8)
        ql.addWidget(section_label("ACTIONS RAPIDES"))
        self.spam_btn=QPushButton("🖱  Spam Click"); self.spam_btn.setCheckable(True)
        self.spam_btn.setStyleSheet(f"background:{BG3};border:1px solid rgba(255,255,255,0.07);border-radius:6px;padding:6px;")
        self.spam_btn.toggled.connect(self._toggle_spam); ql.addWidget(self.spam_btn)
        sort_btn=ghost_btn("📊  Trier barre Windows",lambda: self.logic.sort_taskbar()); ql.addWidget(sort_btn)
        close_btn=QPushButton("✕  Fermer Team")
        close_btn.setStyleSheet(f"background:rgba(224,85,85,0.1);color:{RED};border:1px solid rgba(224,85,85,0.25);border-radius:6px;padding:6px;")
        close_btn.clicked.connect(self._close_team); ql.addWidget(close_btn)
        lay.addWidget(qa_card)
        lay.addStretch()
        return w

    # ── Shortcuts Bar ─────────────────────────────────────────────────────────
    def _mk_shortcuts_bar(self):
        w=QWidget(); w.setStyleSheet(f"background:{BG2};border-top:1px solid rgba(255,255,255,0.05);border-bottom:1px solid rgba(255,255,255,0.05);")
        lay=QVBoxLayout(w); lay.setContentsMargins(20,10,20,10); lay.setSpacing(8)
        lay.addWidget(section_label("RACCOURCIS CLAVIER"))
        grid=QGridLayout(); grid.setHorizontalSpacing(8); grid.setVerticalSpacing(6)
        DEFS=[("Précédent","prev_key"),("Suivant","next_key"),("Rafraîchir","refresh_key"),
              ("Chef","leader_key"),("Afficher/Cacher","toggle_app_key"),("Havre-sac","game_haven_key"),
              ("Sélecteur","selector_key"),("Calibrer","calib_key"),("Inviter","invite_group_key"),
              ("Coller+Valider","paste_active_key")]
        self._sc={}
        for i,(label,key) in enumerate(DEFS):
            r,c=divmod(i,3)
            lb=QLabel(label.upper()); lb.setFont(mono(8)); lb.setStyleSheet(f"color:{MUT};letter-spacing:0.5px;"); grid.addWidget(lb,r,c*3)
            inp=QLineEdit(self.config.get(key,"")); inp.setFixedWidth(70); inp.setFixedHeight(26)
            inp.setStyleSheet(f"background:{BG};border:1px solid rgba(255,255,255,0.07);border-radius:5px;padding:2px 6px;font-size:11px;color:{ACC};font-family:'Space Mono';")
            inp.textChanged.connect(lambda t,k=key:(self.config.set(k,t),self.config.save())); grid.addWidget(inp,r,c*3+1)
            rm=QPushButton("✕"); rm.setFixedSize(16,16); rm.setStyleSheet(f"background:transparent;color:{MUT};border:none;font-size:8px;"); rm.clicked.connect(inp.clear); grid.addWidget(rm,r,c*3+2)
            self._sc[key]=inp
        lay.addLayout(grid)
        return w

    # ── Status Bar ────────────────────────────────────────────────────────────
    def _mk_status_bar(self):
        w=QWidget(); w.setStyleSheet(f"background:{BG};border-top:1px solid rgba(255,255,255,0.05);"); w.setFixedHeight(34)
        lay=QHBoxLayout(w); lay.setContentsMargins(20,0,20,0); lay.setSpacing(16)
        self.scan_msg=QLabel("Prêt — Lance un scan pour détecter les personnages")
        self.scan_msg.setFont(mono(9)); self.scan_msg.setStyleSheet(f"color:{MUT};")
        lay.addWidget(self.scan_msg); lay.addStretch()
        hide=QPushButton("Mini-toolbar  ↓"); hide.setStyleSheet(f"background:transparent;color:{MUT};border:none;font-size:11px;")
        hide.clicked.connect(self._hide_to_mini); lay.addWidget(hide)
        return w

    # ── Account management ────────────────────────────────────────────────────
    def _refresh(self,live=None):
        # STARTUP BEHAVIOR: show empty if no live scan yet
        order=self.config.get("custom_order",[]); classes=self.config.get("classes",{})
        states=self.config.get("accounts_state",{}); teams=self.config.get("accounts_team",{})

        if live is not None:
            # Only show live accounts (detected in Dofus right now)
            merged=sorted(live,key=lambda x:order.index(x["name"]) if x["name"] in order else 999)
        else:
            # No scan yet — show empty state
            merged=[]

        # Clear
        while self.acct_layout.count()>1:
            item=self.acct_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        if not merged:
            self.empty_lbl.setVisible(True); self.acct_scroll.setVisible(False)
            self.count_lbl.setText(""); return

        self.empty_lbl.setVisible(False); self.acct_scroll.setVisible(True)
        for i,acc in enumerate(merged):
            row=AccountRow(acc,self.config,pos_num=i+1)
            row.sig_remove.connect(self._remove)
            row.sig_up.connect(lambda n:(self.logic.move_account(n,-1),self._rescan_refresh()))
            row.sig_down.connect(lambda n:(self.logic.move_account(n,1),self._rescan_refresh()))
            row.sig_leader.connect(self._set_leader)
            self.acct_layout.addWidget(row)

        live_count=len([a for a in merged if a.get("hwnd")])
        self.count_lbl.setText(f"{live_count}/{len(merged)}")
        self.status_badge.setText(f"● {live_count} EN JEU" if live_count>0 else "○ OFFLINE")
        self.status_badge.setStyleSheet(f"background:rgba({'59,185,80' if live_count>0 else '255,255,255'},0.05);color:{'#3fb950' if live_count>0 else MUT};border:1px solid rgba({'59,185,80' if live_count>0 else '255,255,255'},0.15);border-radius:12px;padding:3px 10px;font-family:'Space Mono';font-size:10px;")

    def _rescan_refresh(self):
        """Refresh from current logic state (post-move) without rescanning."""
        if self.logic.all_accounts:
            self._refresh(self.logic.all_accounts)
        else:
            self._refresh([])

    def _scan(self):
        self.scan_msg.setText("Scan en cours..."); self.scan_msg.setStyleSheet(f"color:{MUT};")
        def on_done(accounts):
            self._refresh(accounts)
            lv=len(accounts)
            if lv>0:
                self.scan_msg.setText(f"✅  {lv} fenêtre(s) Dofus détectée(s)"); self.scan_msg.setStyleSheet(f"color:{ACC};font-family:'Space Mono';font-size:9px;")
                self.hk_btn.setText(f"● {lv} EN JEU")
                # Update mini toolbar char icons
                self.mini._rebuild_char_icons(accounts)
            else:
                self.scan_msg.setText("⚠  Aucune fenêtre Dofus — Dofus est-il ouvert ?"); self.scan_msg.setStyleSheet(f"color:#f4a700;font-family:'Space Mono';font-size:9px;")
        t=ScanThread(self.logic); t.done.connect(on_done); t.start(); self._st=t

    def _add_account(self):
        dlg=QDialog(self); dlg.setWindowTitle("Ajouter"); dlg.setFixedSize(300,165); dlg.setStyleSheet(STYLE)
        lay=QVBoxLayout(dlg); lay.setContentsMargins(16,16,16,16); lay.setSpacing(10)
        lay.addWidget(QLabel("Nom :")); ni=QLineEdit(); ni.setPlaceholderText("Ex: Jamaal"); lay.addWidget(ni)
        lay.addWidget(QLabel("Classe :")); cc=QComboBox(); cc.addItems(["— Non définie —"]+CLASSES); lay.addWidget(cc)
        btns=QHBoxLayout(); cancel=ghost_btn("Annuler",dlg.reject); btns.addWidget(cancel)
        ok=accent_btn("Ajouter",dlg.accept); btns.addWidget(ok); lay.addLayout(btns)
        if dlg.exec()==QDialog.DialogCode.Accepted:
            name=ni.text().strip(); cls=cc.currentText()
            if not name: return
            order=self.config.get("custom_order",[])
            if name not in order: order.append(name); self.config.set("custom_order",order)
            if cls and "Non" not in cls:
                c=self.config.get("classes",{}); c[name]=cls; self.config.set("classes",c)
            s=self.config.get("accounts_state",{}); s.setdefault(name,True); self.config.set("accounts_state",s)
            self.config.save(); self._rescan_refresh()

    def _remove(self,name):
        order=self.config.get("custom_order",[])
        if name in order: order.remove(name); self.config.set("custom_order",order)
        self.config.save(); self._rescan_refresh()

    def _set_leader(self,name): self.logic.set_leader(name); self._rescan_refresh()

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

    def _toggle_spam(self,on):
        if not PYAUTOGUI_OK: self.spam_btn.setChecked(False); return
        self._spam=on
        if on:
            iv=self.config.get("spam_click_interval",0.1)
            def _s():
                while self._spam: pyautogui.click(); time.sleep(iv)
            threading.Thread(target=_s,daemon=True).start()
        self.spam_btn.setStyleSheet(f"background:{'rgba(255,138,30,0.15)' if on else BG3};color:{ACC if on else TEXT};border:{'1px solid rgba(255,138,30,0.3)' if on else '1px solid rgba(255,255,255,0.07)'};border-radius:6px;padding:6px;font-weight:{'700' if on else '400'};")

    def _open_char_selector(self):
        accounts = self.logic.get_cycle_list()
        if not accounts: return
        current = None
        lst = self.logic.get_cycle_list()
        if 0 <= self.logic._idx < len(lst): current = lst[self.logic._idx]["name"]
        self._char_selector.show_for(accounts, current)

    def _open_zaap_favorites(self):
        from zaap_favorites import ZaapFavoritesDialog
        ZaapFavoritesDialog(self.config, self).exec()

    def _open_invite(self):
        from invite_dialog import InviteDialog; InviteDialog(self.config,self.logic,self).exec()
    def _open_hunt(self):
        from hunt import HuntDialog; HuntDialog(self.config,self.logic,self).exec()
    def _open_zaap(self):
        from zaap_dialog import ZaapDialog; ZaapDialog(self.config,self.logic,self).exec()
    def _open_calib(self): self._open_calib_zaap()

    def _open_calib_zaap(self):
        from calibrator import CalibrationManager
        if not self.logic.scan_slots():
            QMessageBox.warning(self,"Calibration Zaap","Aucune fenêtre Dofus.\nOuvrez Dofus et scannez d'abord."); return
        self._calib_mgr=CalibrationManager(self.config,self.logic,self,mode="zaap")
        self._calib_mgr.status.connect(lambda m: self.scan_msg.setText(m[:60]))
        self._calib_mgr.finished.connect(lambda:(self.scan_msg.setText("✅  Zaap calibré"),self._rescan_refresh()))
        self._calib_mgr.start()

    def _open_calib_chat(self):
        from calibrator import CalibrationManager
        if not self.logic.scan_slots():
            QMessageBox.warning(self,"Calibration Chat","Aucune fenêtre Dofus.\nOuvrez Dofus et scannez d'abord."); return
        self._calib_mgr=CalibrationManager(self.config,self.logic,self,mode="chat")
        self._calib_mgr.status.connect(lambda m: self.scan_msg.setText(m[:60]))
        self._calib_mgr.finished.connect(lambda:(self.scan_msg.setText("✅  Chat calibré"),self._rescan_refresh()))
        self._calib_mgr.start()

    def _settings(self):
        dlg=QDialog(self); dlg.setWindowTitle("Paramètres avancés"); dlg.setFixedSize(420,240); dlg.setStyleSheet(STYLE)
        lay=QVBoxLayout(dlg); lay.setContentsMargins(16,16,16,16); lay.setSpacing(10)
        lay.addWidget(section_label("CYCLE BINDS  CTRL+F1…F8"))
        binds=self.config.get("cycle_row_binds",[]); grid=QGridLayout(); inps=[]
        for i in range(8):
            grid.addWidget(QLabel(f"Slot {i+1}:"),i//4,(i%4)*2)
            inp=QLineEdit(binds[i] if i<len(binds) else ""); inp.setFixedWidth(82); grid.addWidget(inp,i//4,(i%4)*2+1); inps.append(inp)
        lay.addLayout(grid)
        sr=QHBoxLayout(); sr.addWidget(QLabel("Spam interval (s):")); si=QLineEdit(str(self.config.get("spam_click_interval",0.1))); si.setFixedWidth(60); sr.addWidget(si); sr.addStretch(); lay.addLayout(sr)
        lay.addStretch()
        sv=accent_btn("💾  Sauvegarder",lambda:(None))
        def _sv():
            self.config.set("cycle_row_binds",[i.text().strip() for i in inps])
            try: self.config.set("spam_click_interval",float(si.text()))
            except: pass
            self.config.save(); (self.hk.reload() if self._hk else None); dlg.close()
        sv.clicked.disconnect(); sv.clicked.connect(_sv); lay.addWidget(sv); dlg.exec()

    def _close_team(self):
        r=QMessageBox.question(self,"Fermer Team","Fermer toutes les fenêtres Dofus actives ?",
            QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
        if r==QMessageBox.StandardButton.Yes: self.logic.close_all()

    def closeEvent(self,e): self._spam=False; self.hk.disable(); self.config.save(); e.accept()
    def keyPressEvent(self,e):
        pass  # No Escape handling - avoid accidental window switches

# ── Tray ──────────────────────────────────────────────────────────────────────
class AppTray(QSystemTrayIcon):
    def __init__(self,app,window):
        super().__init__(app); self.window=window
        pix=QPixmap(32,32); pix.fill(QColor(ACC))
        if (SKIN_DIR/"logo.png").exists(): pix=QPixmap(str(SKIN_DIR/"logo.png")).scaled(32,32,Qt.AspectRatioMode.KeepAspectRatio)
        self.setIcon(QIcon(pix)); self.setToolTip(f"{APP_NAME} {VERSION}")
        menu=QMenu(); menu.setStyleSheet(STYLE)
        menu.addAction("▸  Afficher").triggered.connect(window._show_self)
        menu.addAction("▪  Cacher").triggered.connect(window._hide_to_mini)
        menu.addSeparator(); menu.addAction("✕  Quitter").triggered.connect(QApplication.quit)
        self.setContextMenu(menu); self.activated.connect(lambda r: window._show_self() if r==QSystemTrayIcon.ActivationReason.DoubleClick else None)
        self.show()

# ── Entry ─────────────────────────────────────────────────────────────────────
def main():
    tk_root=tk.Tk(); tk_root.withdraw()
    app=QApplication(sys.argv); app.setApplicationName(APP_NAME); app.setQuitOnLastWindowClosed(False)
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
