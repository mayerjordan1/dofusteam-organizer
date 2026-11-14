"""Macro convoi du pack PNJ : complète la macro /zaap de l'Organizer (zaap_macro.send_zaap_command).

Un clic sur un PNJ lance l'enchaînement : /zaap sur chaque suiveur (un par un), /zaap sur le chef, attente d'arrivée,
touche de suivi automatique sur le chef, puis /travel vers le PNJ. Même technique que la macro /zaap existante
(focus de la fenêtre, clic dans le chat calibré « chat_multi », Ctrl+V, Entrée) ; les délais sont réglables.
Échap = arrêt d'urgence. Windows uniquement (pywin32) : les imports sont faits à l'appel.
"""
from __future__ import annotations

import threading

from pnj_engine import Result, convoi_macro_steps


def convoi_names(config, logic):
    """(suiveurs, chef, comptes par nom) d'après les comptes actifs et le nom du chef mémorisé."""
    accounts = {a["name"]: a for a in logic.get_cycle_list()}
    leader = config.get("leader_name", "") or ""
    followers = [n for n in accounts if n != leader]
    return followers, leader, accounts


def run_convoi(config, logic, r: Result, timings: dict, on_status=None, on_done=None) -> bool:
    """Lance la macro dans un thread. Retourne False (sans rien lancer) si le plan est impossible."""
    followers, leader, accounts = convoi_names(config, logic)
    if leader not in accounts:
        if on_status:
            on_status("⚠ Chef introuvable : fais un scan des fenêtres et choisis le chef.")
        return False
    chat_positions = config.get("macro_positions", {}).get("chat_positions", {})
    missing = [n for n in [leader] + followers if n not in chat_positions]
    if missing:
        if on_status:
            on_status("⚠ Chat non calibré : " + ", ".join(missing) + " (Calibration → Chat 3.7)")
        return False
    steps = convoi_macro_steps(r, followers, leader, timings)

    def _run():
        import time
        import pyautogui
        import pyperclip
        import win32gui
        import zaap_macro as zm

        abort = [False]
        stop = threading.Event()
        zm.start_kill_switch(abort, stop, on_status=on_status)

        def focus(name):
            hwnd = accounts[name]["hwnd"]
            logic.focus_window(hwnd)
            for _ in range(15):
                try:
                    if win32gui.GetForegroundWindow() == hwnd:
                        break
                except Exception:
                    pass
                time.sleep(0.1)
            time.sleep(zm._jitter(0.08))
            return hwnd

        def paste(name, text):
            hwnd = focus(name)
            pyperclip.copy(text)
            ax, ay = zm.rel_to_abs(hwnd, *chat_positions[name])
            pyautogui.click(ax, ay)
            time.sleep(zm._jitter(0.12))
            pyautogui.hotkey("ctrl", "v")
            time.sleep(zm._jitter(0.15))
            pyautogui.press("enter")

        def key(name, combo):
            focus(name)
            parts = [p.strip().lower() for p in combo.split("+") if p.strip()]
            if len(parts) == 2 and parts[0] == "ctrl" and len(parts[1]) == 1:
                zm._send_ctrl_combo_sendinput(parts[1])        # même méthode que le Ctrl+W de la macro /zaap
            elif parts:
                pyautogui.hotkey(*parts)

        zm.freeze_mouse()
        try:
            total = len(steps)
            for i, st in enumerate(steps):
                if abort[0]:
                    break
                if st["do"] == "wait":
                    zm.unfreeze_mouse()                          # pendant les attentes la souris est libre
                    if on_status:
                        on_status(f"⏳ {st['label']} ({st['s']:.1f}s)")
                    end = time.time() + st["s"]
                    while time.time() < end and not abort[0]:
                        time.sleep(0.05)
                    zm.freeze_mouse()
                    continue
                if on_status:
                    what = st.get("text") or st.get("key")
                    on_status(f"[{i + 1}/{total}] {st['who']} : {what}")
                try:
                    paste(st["who"], st["text"]) if st["do"] == "paste" else key(st["who"], st["key"])
                except Exception as e:  # noqa: BLE001
                    if on_status:
                        on_status(f"⚠ {st['who']} : {e}")
        finally:
            stop.set()
            zm.unfreeze_mouse()
        if on_status and not abort[0]:
            on_status(f"✅ Convoi vers {r.name} terminé")
        if on_done:
            on_done()

    threading.Thread(target=_run, daemon=True).start()
    return True
