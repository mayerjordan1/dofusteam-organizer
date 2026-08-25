"""
DofusTeam — logic.py
Gestion des fenêtres Dofus Unity/Rétro
"""
import win32gui, win32con, win32process, win32api, ctypes, time, threading

class DofusLogic:
    def __init__(self, config):
        self.config = config
        self.all_accounts = []
        self.leader_hwnd  = None
        self._idx         = 0

    # ── Scan ──────────────────────────────────────────────────────────────────

    def scan_slots(self):
        version = self.config.get("game_version", "Unity")
        raw = []

        def cb(hwnd, _):
            if not win32gui.IsWindowVisible(hwnd): return True
            title = win32gui.GetWindowText(hwnd).strip()
            if not title: return True
            cls = win32gui.GetClassName(hwnd)
            if version == "Unity":
                if cls == "UnityWndClass":
                    raw.append((hwnd, title))
            else:
                if "Dofus Retro" in title:
                    raw.append((hwnd, title))
            return True

        win32gui.EnumWindows(cb, None)

        accounts = []
        for hwnd, title in raw:
            if version == "Unity":
                # Skip the Dofus launcher/updater window
                if title.lower().startswith("dofus"): continue
                parts = title.split(" - ")
                pseudo = parts[0].strip()
                # Classe is in the title OR stored in config
                if len(parts) > 1:
                    classe = parts[1].strip()
                    c = self.config.get("classes", {})
                    c[pseudo] = classe
                    self.config.set("classes", c)
                else:
                    classe = self.config.get("classes", {}).get(pseudo, "Inconnu")
            else:
                pseudo = title.split(" - Dofus Retro")[0].strip()
                classe = self.config.get("classes", {}).get(pseudo, "Inconnu")

            active = self.config.get("accounts_state", {}).get(pseudo, True)
            team   = self.config.get("accounts_team",  {}).get(pseudo, "Team 1")
            accounts.append({"name": pseudo, "hwnd": hwnd, "active": active, "team": team, "classe": classe})

        # Add to order if new
        order = self.config.get("custom_order", [])
        for acc in accounts:
            if acc["name"] not in order:
                order.append(acc["name"])
        self.config.set("custom_order", order)
        self.config.save()

        # Sort by order
        self.all_accounts = sorted(accounts, key=lambda x: order.index(x["name"]) if x["name"] in order else 999)

        # Update leader hwnd
        self.leader_hwnd = None
        leader = self.config.get("leader_name", "")
        for acc in self.all_accounts:
            if acc["name"] == leader:
                self.leader_hwnd = acc["hwnd"]

        return self.all_accounts

    def debug_all_windows(self):
        """Returns all visible windows for debugging."""
        result = []
        def cb(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                t = win32gui.GetWindowText(hwnd)
                c = win32gui.GetClassName(hwnd)
                if t: result.append((c, t, hwnd))
            return True
        win32gui.EnumWindows(cb, None)
        return result

    # ── Cycle ─────────────────────────────────────────────────────────────────

    def get_cycle_list(self):
        mode = self.config.get("current_mode", "ALL")
        return [a for a in self.all_accounts
                if a["active"] and (mode == "ALL" or a["team"] == mode)]

    # ── Focus ──────────────────────────────────────────────────────────────────

    def focus_window(self, hwnd):
        if not hwnd: return
        try:
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            ctypes.windll.user32.AllowSetForegroundWindow(pid)
            ctypes.windll.user32.keybd_event(0x12, 0, 0, 0)
            ctypes.windll.user32.keybd_event(0x12, 0, 2, 0)
            win32gui.SetForegroundWindow(hwnd)
        except Exception as e:
            print(f"[focus] {e}")

    def switch_next(self):
        lst = self.get_cycle_list()
        if not lst: return
        self._idx = (self._idx + 1) % len(lst)
        self.focus_window(lst[self._idx]["hwnd"])

    def switch_prev(self):
        lst = self.get_cycle_list()
        if not lst: return
        self._idx = (self._idx - 1) % len(lst)
        self.focus_window(lst[self._idx]["hwnd"])

    def switch_to_leader(self):
        if self.leader_hwnd:
            self.focus_window(self.leader_hwnd)

    def switch_to_index(self, idx):
        lst = self.get_cycle_list()
        if 0 <= idx < len(lst):
            self._idx = idx
            self.focus_window(lst[idx]["hwnd"])

    def switch_to_name(self, name):
        for i, acc in enumerate(self.get_cycle_list()):
            if acc["name"] == name:
                self._idx = i
                self.focus_window(acc["hwnd"])
                return

    # ── Reorder ───────────────────────────────────────────────────────────────

    def _sync_order(self, active_list):
        order = self.config.get("custom_order", [])
        indices = [order.index(a["name"]) for a in active_list if a["name"] in order]
        names   = [a["name"] for a in active_list if a["name"] in order]
        for i, name in zip(sorted(indices), names):
            order[i] = name
        self.config.set("custom_order", order)
        self.config.save()
        self.all_accounts.sort(key=lambda x: order.index(x["name"]) if x["name"] in order else 999)

    def move_account(self, name, direction):
        active = self.get_cycle_list()
        names  = [a["name"] for a in active]
        if name not in names: return
        idx = names.index(name)
        new = idx + direction
        if 0 <= new < len(active):
            active[idx], active[new] = active[new], active[idx]
            self._sync_order(active)

    # ── Settings ──────────────────────────────────────────────────────────────

    def toggle_active(self, name, v):
        for a in self.all_accounts:
            if a["name"] == name: a["active"] = v
        s = self.config.get("accounts_state", {})
        s[name] = v
        self.config.set("accounts_state", s)
        self.config.save()

    def set_team(self, name, team):
        for a in self.all_accounts:
            if a["name"] == name: a["team"] = team
        t = self.config.get("accounts_team", {})
        if team: t[name] = team
        else: t.pop(name, None)
        self.config.set("accounts_team", t)
        self.config.save()

    def set_leader(self, name):
        self.config.set("leader_name", name)
        self.config.save()
        self.leader_hwnd = None
        for a in self.all_accounts:
            if a["name"] == name:
                self.leader_hwnd = a["hwnd"]

    def set_mode(self, mode):
        self.config.set("current_mode", mode)
        self.config.save()

    # ── Actions ───────────────────────────────────────────────────────────────

    def refresh_all(self):
        for acc in self.get_cycle_list():
            try: win32api.PostMessage(acc["hwnd"], win32con.WM_KEYDOWN, win32con.VK_F5, 0)
            except: pass

    def sort_taskbar(self):
        active = self.get_cycle_list()
        if not active: return
        def _s():
            for a in active: win32gui.ShowWindow(a["hwnd"], win32con.SW_HIDE)
            time.sleep(0.3)
            for a in active:
                win32gui.ShowWindow(a["hwnd"], win32con.SW_SHOW)
                time.sleep(0.1)
            if self.leader_hwnd: self.focus_window(self.leader_hwnd)
        threading.Thread(target=_s, daemon=True).start()

    def close_window(self, hwnd):
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            h = ctypes.windll.kernel32.OpenProcess(1, False, pid)
            ctypes.windll.kernel32.TerminateProcess(h, 0)
            ctypes.windll.kernel32.CloseHandle(h)
        except: pass

    def close_all(self):
        for acc in self.get_cycle_list():
            self.close_window(acc["hwnd"])
