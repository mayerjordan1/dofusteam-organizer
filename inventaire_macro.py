"""
DofusTeam — inventaire_macro.py
Macro "Inventaire" : le raccourci est déjà bind côté jeu (comme la potion de
rappel) — pas besoin de calibrer une position. La macro se contente de passer
sur chaque fenêtre active (switch + focus confirmé) et de renvoyer ce même
raccourci clavier, avant de revenir sur le chef. Même pattern que
recall_macro.quick_recall_potion.
"""
import time, threading

try:
    import keyboard as _kb
    KEYBOARD_OK = True
except ImportError:
    KEYBOARD_OK = False

try:
    import win32gui
    WINDOWS = True
except ImportError:
    WINDOWS = False


def quick_inventaire(config, logic, key, on_status=None, on_done=None):
    """Pour chaque perso actif : focus (avec confirmation) + renvoi du raccourci
    inventaire. Revient sur le chef à la fin."""
    if not KEYBOARD_OK or not key:
        if on_status: on_status("❌ raccourci ou module keyboard manquant")
        if on_done: on_done()
        return

    def _run():
        try:
            accounts = logic.get_cycle_list()
            if not accounts:
                if on_status: on_status("⚠ Aucun compte actif")
                return

            if on_status: on_status(f"🎒 Inventaire sur {len(accounts)} perso(s)...")
            for acc in accounts:
                hwnd = acc["hwnd"]
                logic.focus_window(hwnd)
                for _ in range(15):
                    try:
                        if win32gui.GetForegroundWindow() == hwnd: break
                    except Exception:
                        pass
                    time.sleep(0.1)
                time.sleep(0.08)
                try:
                    _kb.send(key)
                except Exception as e:
                    if on_status: on_status(f"⚠ Inventaire {acc['name']}: {e}")
                time.sleep(0.15)

            logic.switch_to_leader()
            if on_status: on_status("✅ Inventaire ouvert sur tous !")
        finally:
            if on_done: on_done()

    threading.Thread(target=_run, daemon=True).start()
