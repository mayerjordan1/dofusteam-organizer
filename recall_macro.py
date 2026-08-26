"""
DofusTeam — recall_macro.py
Macro "potion de rappel" : le raccourci est déjà bind côté jeu (Dofus détecte
tout seul la potion de rappel dans l'inventaire, pas besoin de calibrer une
position). La macro se contente de passer sur chaque fenêtre active
(switch + focus confirmé) et de renvoyer ce même raccourci clavier.
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


def quick_recall_potion(config, logic, key, on_status=None, on_done=None):
    """Pour chaque perso actif : focus (avec confirmation) + renvoi du raccourci
    de potion de rappel. Revient sur le chef à la fin.
    `on_done` est appelé en fin de thread (même en cas d'erreur) — sert de
    verrou côté appelant pour éviter qu'un renvoi du même raccourci dans le jeu
    (capté par le hook clavier global) ne redéclenche la macro en boucle."""
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

            if on_status: on_status(f"🧪 Potion de rappel sur {len(accounts)} perso(s)...")
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
                    if on_status: on_status(f"⚠ Potion {acc['name']}: {e}")
                time.sleep(0.15)

            logic.switch_to_leader()
            if on_status: on_status("✅ Potion de rappel envoyée à tous !")
        finally:
            if on_done: on_done()

    threading.Thread(target=_run, daemon=True).start()
