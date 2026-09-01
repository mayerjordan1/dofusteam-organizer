
import ctypes as _ctypes

def _send_key_sendinput(key_char):
    """Most reliable key injection via SendInput (bypasses all hooks)."""
    class KEYBDINPUT(_ctypes.Structure):
        _fields_=[('wVk',_ctypes.c_ushort),('wScan',_ctypes.c_ushort),('dwFlags',_ctypes.c_ulong),
                  ('time',_ctypes.c_ulong),('dwExtraInfo',_ctypes.c_void_p)]
    class INPUT(_ctypes.Structure):
        class _I(_ctypes.Union):
            _fields_=[('ki',KEYBDINPUT)]
        _anonymous_=('_i',); _fields_=[('type',_ctypes.c_ulong),('_i',_I)]
    vk=ord(key_char.upper())
    inp=INPUT(type=1); inp.ki.wVk=vk; inp.ki.dwFlags=0
    _ctypes.windll.user32.SendInput(1,_ctypes.pointer(inp),_ctypes.sizeof(inp))
    import time; time.sleep(0.06)
    inp.ki.dwFlags=0x0002  # KEYEVENTF_KEYUP
    _ctypes.windll.user32.SendInput(1,_ctypes.pointer(inp),_ctypes.sizeof(inp))


def _send_ctrl_combo_sendinput(key_char):
    """Ctrl+<touche> injecté via SendInput plutôt que pyautogui.hotkey —
    même technique que _send_key_sendinput ci-dessus (déjà utilisée pour H
    car pyautogui.press n'était pas fiable avec le client Dofus). Le Ctrl+W
    de réactivation d'autofollow en fin de macro zaap ne prenait jamais côté
    utilisateur alors qu'il marche à la main ou via sa propre macro souris —
    ce contournement est le même que celui déjà validé pour le havre-sac."""
    class KEYBDINPUT(_ctypes.Structure):
        _fields_=[('wVk',_ctypes.c_ushort),('wScan',_ctypes.c_ushort),('dwFlags',_ctypes.c_ulong),
                  ('time',_ctypes.c_ulong),('dwExtraInfo',_ctypes.c_void_p)]
    class INPUT(_ctypes.Structure):
        class _I(_ctypes.Union):
            _fields_=[('ki',KEYBDINPUT)]
        _anonymous_=('_i',); _fields_=[('type',_ctypes.c_ulong),('_i',_I)]
    import time as _time
    VK_CONTROL=0x11
    vk_key=ord(key_char.upper())
    def _press(vk, down):
        inp=INPUT(type=1); inp.ki.wVk=vk; inp.ki.dwFlags=0 if down else 0x0002
        _ctypes.windll.user32.SendInput(1,_ctypes.pointer(inp),_ctypes.sizeof(inp))
    _press(VK_CONTROL, True);  _time.sleep(0.03)
    _press(vk_key, True);      _time.sleep(0.06)
    _press(vk_key, False);     _time.sleep(0.03)
    _press(VK_CONTROL, False)

"""
DofusTeam — zaap_macro.py
Système Auto-Zaap : calibration + exécution en 3 phases
"""

import time
import random
import threading
import ctypes
import win32gui
import win32api
import pyautogui

pyautogui.FAILSAFE = False


def _jitter(base, pct=0.3):
    """Délai avec variation aléatoire — casse la régularité robotique
    (Dofus peut repérer des actions trop identiques d'une fenêtre à l'autre)
    sans ralentir la moyenne."""
    return max(0.05, base * random.uniform(1 - pct, 1 + pct))


# ── Mouse freeze ──────────────────────────────────────────────────────────────

def freeze_mouse():
    """Bloque la souris (nécessite admin, sinon silencieux)."""
    try:
        ctypes.windll.user32.BlockInput(True)
    except:
        pass

def unfreeze_mouse():
    try:
        ctypes.windll.user32.BlockInput(False)
    except:
        pass


_VK_ESCAPE = 0x1B


def start_kill_switch(abort_flag, stop_watching, on_status=None):
    """Coupe-circuit d'urgence partagé par les macros zaap "quick" (toolbar).

    Pendant freeze_mouse()/BlockInput(True), le clic/clavier normal ne
    déclenche plus rien dans l'app (y compris un éventuel bouton Arrêter) —
    ces macros n'en ont même pas. GetAsyncKeyState lit l'état matériel de
    la touche directement, hors de la file de messages Windows que
    BlockInput bloque, donc Échap reste le seul moyen fiable d'interrompre
    la macro en cours.

    abort_flag : liste à 1 élément (ex: [False]) — mise à True si Échap est
    pressé ; la macro appelante doit la vérifier entre chaque action.
    stop_watching : threading.Event — à set() par l'appelant une fois la
    macro terminée (normalement ou non), pour arrêter le thread de veille
    au lieu de le laisser tourner indéfiniment."""
    def _watch():
        while not stop_watching.is_set():
            if win32api.GetAsyncKeyState(_VK_ESCAPE) & 0x8000:
                abort_flag[0] = True
                unfreeze_mouse()
                if on_status:
                    on_status("⛔ Arrêt d'urgence (Échap).")
                return
            time.sleep(0.05)
    threading.Thread(target=_watch, daemon=True).start()


# ── Relative coords helpers ───────────────────────────────────────────────────

def abs_to_rel(hwnd, ax, ay):
    """Convertit des coordonnées absolues en relatives à la fenêtre."""
    rect = win32gui.GetWindowRect(hwnd)
    w = rect[2] - rect[0]
    h = rect[3] - rect[1]
    if w <= 0 or h <= 0:
        return None
    return ((ax - rect[0]) / w, (ay - rect[1]) / h)

def rel_to_abs(hwnd, rx, ry):
    """Convertit des coordonnées relatives en absolues."""
    rect = win32gui.GetWindowRect(hwnd)
    w = rect[2] - rect[0]
    h = rect[3] - rect[1]
    return (int(rect[0] + w * rx), int(rect[1] + h * ry))


# ── Calibration capture ───────────────────────────────────────────────────────

class ZaapCalibrator:
    """
    Capture la position du zaap pour un personnage donné.
    Usage :
        calib = ZaapCalibrator(hwnd, on_done_callback)
        calib.start()   # attend 3s puis capture le prochain clic
    """
    def __init__(self, hwnd, name, on_done):
        self.hwnd    = hwnd
        self.name    = name
        self.on_done = on_done  # fn(name, rx, ry) ou fn(name, None, None) si annulé
        self._active = False

    def start(self):
        self._active = True
        threading.Thread(target=self._wait_click, daemon=True).start()

    def cancel(self):
        self._active = False

    def _wait_click(self):
        """Attend un clic gauche et capture sa position."""
        # Attendre relâchement de tout bouton actuel
        time.sleep(0.3)
        while self._active:
            if win32api.GetAsyncKeyState(0x01) & 0x8000:  # LMB pressed
                ax, ay = win32api.GetCursorPos()
                rel = abs_to_rel(self.hwnd, ax, ay)
                self._active = False
                if rel:
                    self.on_done(self.name, rel[0], rel[1])
                else:
                    self.on_done(self.name, None, None)
                return
            time.sleep(0.02)
        self.on_done(self.name, None, None)


# ── Zaap Executor ─────────────────────────────────────────────────────────────

class ZaapExecutor:
    """
    Exécute la macro auto-zaap en 3 phases.

    Phase 1 : Pour chaque perso actif → H + clic zaap calibré
    Phase 2 : Pause — l'utilisateur tape la destination + Ctrl+A + Ctrl+C
    Phase 3 : Sur les persos suivants → Ctrl+V + Entrée
    """

    def __init__(self, config, logic, on_status=None, on_phase2_ready=None, on_done=None):
        self.config          = config
        self.logic           = logic
        self.on_status       = on_status        # fn(str) — message de progression
        self.on_phase2_ready = on_phase2_ready  # fn() — prévient que phase 2 peut commencer
        self.on_done         = on_done          # fn() — macro terminée
        self._running        = False
        self._phase3_event   = threading.Event()

    def _status(self, msg):
        if self.on_status:
            self.on_status(msg)

    def start(self):
        """Lance la phase 1 dans un thread."""
        self._running = True
        self._phase3_event.clear()
        threading.Thread(target=self._run, daemon=True).start()
        threading.Thread(target=self._watch_kill_switch, daemon=True).start()

    def trigger_phase3(self):
        """Appelé par l'UI quand l'utilisateur a fini la phase 2."""
        self._phase3_event.set()

    def stop(self):
        self._running = False
        self._phase3_event.set()  # débloquer si en attente
        unfreeze_mouse()  # immédiat — ne pas attendre que _run() repasse par son check périodique

    def _watch_kill_switch(self):
        """Touche Échap = coupe-circuit d'urgence.

        freeze_mouse() (BlockInput) bloque tout clic/frappe au niveau
        système pendant les phases 1/3 — y compris sur le bouton "Arrêter"
        de l'UI, qui devient donc inatteignable. GetAsyncKeyState lit
        l'état matériel de la touche directement (pas la file de messages
        Windows que BlockInput intercepte), donc reste utilisable même
        dans cet état : c'est le seul moyen d'interrompre la macro une
        fois lancée."""
        VK_ESCAPE = 0x1B
        while self._running:
            if win32api.GetAsyncKeyState(VK_ESCAPE) & 0x8000:
                self._status("⛔ Arrêt d'urgence (Échap).")
                self.stop()
                if self.on_done:
                    self.on_done()
                return
            time.sleep(0.05)

    def _run(self):
        accounts = self.logic.get_cycle_list()
        if not accounts:
            self._status("Aucun compte actif détecté.")
            if self.on_done: self.on_done()
            return

        zaaps     = self.config.get("macro_positions", {}).get("zaaps", {})
        havresacs = self.config.get("macro_positions", {}).get("havresacs", {})
        delay_h = float(self.config.get("zaap_open_delay", 0.8))   # délai après H
        delay_z = float(self.config.get("zaap_click_delay", 0.5))  # délai après clic zaap

        # ── PHASE 1 : Ouvrir tous les havresacs + zaap ───────────────────────
        self._status("Phase 1 — Ouverture des havresacs...")
        freeze_mouse()

        for i, acc in enumerate(accounts):
            if not self._running:
                unfreeze_mouse()
                return

            name = acc["name"]
            hwnd = acc["hwnd"]
            coords = zaaps.get(name)
            hs_coords = havresacs.get(name)

            self._status(f"Phase 1 [{i+1}/{len(accounts)}] — {name}")

            # Focus fenêtre — on attend la confirmation réelle du focus
            # (sinon on peut cliquer/taper sur la fenêtre précédente si le
            # switch est lent, ex: rendu jeu, fenêtre minimisée).
            self.logic.focus_window(hwnd)
            for _ in range(15):
                try:
                    if win32gui.GetForegroundWindow() == hwnd: break
                except: pass
                time.sleep(0.1)
            time.sleep(_jitter(0.08))

            # Ouvrir le havre-sac : clic sur l'icône calibrée si dispo
            # (fallback si la touche H ne marche pas), sinon touche H
            if hs_coords:
                try:
                    ax, ay = rel_to_abs(hwnd, hs_coords[0], hs_coords[1])
                    pyautogui.click(ax, ay)
                except Exception as e:
                    self._status(f"Erreur clic havre-sac {name}: {e}")
            else:
                haven_key = self.config.get("game_haven_key", "h")
                pyautogui.press(haven_key)
            time.sleep(_jitter(delay_h))

            # Clic sur le zaap calibré
            if coords:
                rx, ry = coords
                try:
                    ax, ay = rel_to_abs(hwnd, rx, ry)
                    pyautogui.click(ax, ay)
                    time.sleep(_jitter(delay_z))
                except Exception as e:
                    self._status(f"Erreur clic zaap {name}: {e}")
            else:
                self._status(f"⚠ {name} — zaap non calibré, ignoré")
                time.sleep(_jitter(0.3))

        unfreeze_mouse()

        # ── PHASE 2 : Pause utilisateur ──────────────────────────────────────
        self._status(
            "Phase 2 — Allez sur le 1er perso, tapez la destination,\n"
            "faites Ctrl+A puis Ctrl+C, puis cliquez Exécuter !"
        )
        if self.on_phase2_ready:
            self.on_phase2_ready()

        # Attendre que l'utilisateur clique "Exécuter"
        self._phase3_event.wait()
        if not self._running:
            if self.on_done: self.on_done()
            return

        # ── PHASE 3 : Coller la destination sur tous les autres ──────────────
        self._status("Phase 3 — Envoi de la destination...")
        freeze_mouse()

        # Récupère le chat_position pour la saisie de destination
        chat_pos = self.config.get("macro_positions", {}).get("chat_position")
        delay_p  = float(self.config.get("zaap_paste_delay", 0.4))

        for i, acc in enumerate(accounts):
            if not self._running:
                break
            name = acc["name"]
            hwnd = acc["hwnd"]
            self._status(f"Phase 3 [{i+1}/{len(accounts)}] — {name}")

            self.logic.focus_window(hwnd)
            for _ in range(15):
                try:
                    if win32gui.GetForegroundWindow() == hwnd: break
                except: pass
                time.sleep(0.1)
            time.sleep(_jitter(0.08))

            # Coller dans le champ de recherche du zaap
            pyautogui.hotkey("ctrl", "a")
            time.sleep(_jitter(0.1))
            pyautogui.hotkey("ctrl", "v")
            time.sleep(_jitter(0.2))
            pyautogui.press("enter")
            time.sleep(_jitter(delay_p))

        # Revenir sur le chef de groupe une fois la macro finie (même
        # comportement que les autres macros zaap) + Ctrl+W pour réactiver
        # l'autofollow une fois de retour sur le chef.
        leader_hwnd = getattr(self.logic, "leader_hwnd", None)
        if leader_hwnd:
            self.logic.focus_window(leader_hwnd)
            for _ in range(15):
                try:
                    if win32gui.GetForegroundWindow() == leader_hwnd: break
                except Exception: pass
                time.sleep(0.1)
            time.sleep(_jitter(0.35))
            try: _send_ctrl_combo_sendinput("w")
            except Exception: pass

        unfreeze_mouse()
        self._status("✅ Auto-zaap terminé !")
        self._running = False
        if self.on_done: self.on_done()


# ── Quick macros accessible from toolbar ─────────────────────────────────────

def quick_havresac_zaap(config, logic, on_status=None):
    """
    Macro havre-sac + zaap — même workflow que la main :
    
    Phase 1 (H rapide sur tous):
      → switch fenetre → H → switch → H → switch → H...
      Pas d'attente entre les H, les havre-sacs chargent en parallèle
    
    Phase 2 (après délai = havre-sacs chargés):
      → switch fenetre → clic zaap → switch → clic → ...
    """
    import time, threading, random
    try: import pyautogui, win32gui, win32api
    except ImportError:
        if on_status: on_status("❌ dépendances manquantes"); return

    def _run():
        accounts   = logic.get_cycle_list()
        if not accounts:
            if on_status: on_status("⚠ Aucun compte actif"); return

        zaaps      = config.get("macro_positions", {}).get("zaaps", {})
        havresacs  = config.get("macro_positions", {}).get("havresacs", {})
        haven_key  = config.get("game_haven_key", "h")
        open_delay = float(config.get("zaap_open_delay", 1.0))

        abort_flag = [False]
        stop_watching = threading.Event()
        start_kill_switch(abort_flag, stop_watching, on_status=on_status)

        try: import ctypes; ctypes.windll.user32.BlockInput(True)
        except: pass

        # ── Phase 1 : Havre-sac sur chaque fenetre (rapide, sans attente) ──
        if on_status: on_status("Phase 1 — Ouverture havresacs (×" + str(len(accounts)) + ")")
        for acc in accounts:
            if abort_flag[0]:
                stop_watching.set()
                return
            name = acc["name"]; hwnd = acc["hwnd"]
            logic.focus_window(hwnd)
            # Attendre confirmation focus (max 1.5s)
            for _ in range(15):
                try:
                    if win32gui.GetForegroundWindow() == hwnd: break
                except: pass
                time.sleep(0.1)
            time.sleep(_jitter(0.08))
            # Clic sur l'icône calibrée si dispo (fallback si H ne marche pas),
            # sinon touche H
            hs_coords = havresacs.get(name)
            if hs_coords:
                try:
                    rect = win32gui.GetWindowRect(hwnd)
                    w = rect[2]-rect[0]; h = rect[3]-rect[1]
                    rx, ry = hs_coords
                    pyautogui.click(int(rect[0]+w*rx), int(rect[1]+h*ry))
                except Exception as e:
                    print(f"[hsac] click err: {e}")
            else:
                try:
                    _send_key_sendinput(haven_key)
                except Exception as e:
                    print(f"[hsac] key err: {e}")
                    try:
                        import keyboard as _kb; _kb.send(haven_key)
                    except: pyautogui.press(haven_key)
            time.sleep(_jitter(0.12))  # switch rapide vers le suivant

        # ── Attente chargement havre-sacs ──────────────────────────────────
        if on_status: on_status(f"⏳ Chargement havresacs... ({open_delay}s)")
        time.sleep(open_delay)

        # ── Phase 2 : Clic zaap sur chaque fenetre ─────────────────────────
        if on_status: on_status("Phase 2 — Clic zaaps")
        for acc in accounts:
            if abort_flag[0]:
                stop_watching.set()
                return
            name = acc["name"]; hwnd = acc["hwnd"]
            logic.focus_window(hwnd)
            for _ in range(15):
                try:
                    if win32gui.GetForegroundWindow() == hwnd: break
                except: pass
                time.sleep(0.08)
            time.sleep(_jitter(0.1))
            if name in zaaps:
                try:
                    rect = win32gui.GetWindowRect(hwnd)
                    w = rect[2]-rect[0]; h = rect[3]-rect[1]
                    rx,ry = zaaps[name]
                    pyautogui.click(int(rect[0]+w*rx), int(rect[1]+h*ry))
                except Exception as e:
                    if on_status: on_status(f"⚠ Zaap {name}: {e}")
            else:
                if on_status: on_status(f"⚠ {name} non calibré")
            time.sleep(_jitter(0.2))

        stop_watching.set()
        try: import ctypes; ctypes.windll.user32.BlockInput(False)
        except: pass
        if on_status: on_status("✅ Havresacs + zaaps ouverts — Copie la destination !")

    threading.Thread(target=_run, daemon=True).start()


def quick_paste_zaap(config, logic, on_status=None):
    """
    Bouton 2 toolbar :
    Pour chaque fenêtre : Ctrl+A + Ctrl+V + Entrée
    (l'utilisateur a déjà copié la destination)
    """
    import time, threading, random
    try:
        import pyautogui, win32gui
        pyautogui.FAILSAFE = False
    except ImportError:
        if on_status: on_status("❌ pyautogui/win32gui manquant")
        return

    def _run():
        accounts = logic.get_cycle_list()
        if not accounts:
            if on_status: on_status("⚠ Aucun compte actif"); return

        paste_delay = float(config.get("zaap_paste_delay", 0.35))

        try:
            original_fg_hwnd = win32gui.GetForegroundWindow()
        except Exception:
            original_fg_hwnd = None

        abort_flag = [False]
        stop_watching = threading.Event()
        start_kill_switch(abort_flag, stop_watching, on_status=on_status)

        try: import ctypes; ctypes.windll.user32.BlockInput(True)
        except: pass

        try:
            if on_status: on_status("📋 Collage de la destination...")
            for i,acc in enumerate(accounts):
                if abort_flag[0]:
                    break
                hwnd = acc["hwnd"]
                logic.focus_window(hwnd)
                # Attend la confirmation réelle du focus avant de coller —
                # sinon un switch lent fait coller/valider sur le mauvais
                # perso ("saute des fenêtres").
                for _ in range(15):
                    try:
                        if win32gui.GetForegroundWindow() == hwnd: break
                    except: pass
                    time.sleep(0.1)
                time.sleep(_jitter(0.08))
                pyautogui.hotkey("ctrl","v")
                time.sleep(_jitter(0.1))
                pyautogui.press("enter")
                time.sleep(max(paste_delay, _jitter(0.15)))
                if on_status: on_status(f"📋 {i+1}/{len(accounts)} — {acc['name']}")
        finally:
            stop_watching.set()
            # Retour au chef de groupe (ou à la fenêtre d'origine à défaut) —
            # évite de rester bloqué sur le dernier perso collé.
            leader_hwnd = getattr(logic, "leader_hwnd", None)
            if leader_hwnd:
                logic.focus_window(leader_hwnd)
                for _ in range(15):
                    try:
                        if win32gui.GetForegroundWindow() == leader_hwnd: break
                    except: pass
                    time.sleep(0.1)
                time.sleep(_jitter(0.35))
                # Ctrl+W réactive l'autofollow (raccourci Dofus) une fois de
                # retour sur le chef, pour reprendre le suivi auto du groupe.
                try: pyautogui.hotkey("ctrl", "w")
                except Exception: pass
            elif original_fg_hwnd:
                logic.focus_window(original_fg_hwnd)
            try: import ctypes; ctypes.windll.user32.BlockInput(False)
            except: pass

        if on_status: on_status("✅ Destination collée sur tous les persos !")

    threading.Thread(target=_run, daemon=True).start()
