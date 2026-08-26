"""
DofusTeam — inventaire_macro.py
Macro générique à position calibrée : passe sur chaque fenêtre active
(switch + focus confirmé) et clique sur la position calibrée pour ce perso
(ex: icône inventaire). Position relative à la fenêtre, calibrée une fois par
perso via calibrator.py mode='inventaire' — même pattern que
zaap_favorites.run_zaap_to_destination.
"""
import time, threading

try:
    import pyautogui
    pyautogui.FAILSAFE = False
    MACRO_OK = True
except ImportError:
    MACRO_OK = False

try:
    import win32gui
    WINDOWS = True
except ImportError:
    WINDOWS = False


def quick_inventaire(config, logic, on_status=None):
    """Pour chaque perso actif calibré : focus (avec confirmation) + clic sur la
    position calibrée. Revient sur le chef à la fin."""
    if not MACRO_OK:
        if on_status: on_status("❌ pyautogui manquant")
        return

    def _run():
        accounts = logic.get_cycle_list()
        if not accounts:
            if on_status: on_status("⚠ Aucun compte actif")
            return

        positions = config.get("macro_positions", {}).get("inventaire", {})
        if not positions:
            if on_status: on_status("⚠ Inventaire non calibré (clic droit sur le bouton)")
            return

        if on_status: on_status(f"🎒 Inventaire sur {len(accounts)} perso(s)...")
        for acc in accounts:
            name = acc["name"]; hwnd = acc["hwnd"]
            if name not in positions:
                if on_status: on_status(f"⚠ {name} non calibré — ignoré")
                continue
            logic.focus_window(hwnd)
            for _ in range(15):
                try:
                    if win32gui.GetForegroundWindow() == hwnd: break
                except Exception:
                    pass
                time.sleep(0.1)
            time.sleep(0.1)
            try:
                rect = win32gui.GetWindowRect(hwnd)
                w = rect[2] - rect[0]; h = rect[3] - rect[1]
                rx, ry = positions[name]
                pyautogui.click(int(rect[0] + w * rx), int(rect[1] + h * ry))
            except Exception as e:
                if on_status: on_status(f"⚠ Inventaire {name}: {e}")
            time.sleep(0.25)

        logic.switch_to_leader()
        if on_status: on_status("✅ Inventaire ouvert/cliqué sur tous !")

    threading.Thread(target=_run, daemon=True).start()
